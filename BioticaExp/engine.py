
from controller import MainController
from openai import OpenAI
from typing_extensions import override
from openai import AssistantEventHandler
from tools import tools

import requests

import time
from datetime import datetime
import json
import os
import logging
import threading

from dotenv import load_dotenv

load_dotenv()

# Configure the logger
logging.basicConfig(
    filename='agent.log',
    level=logging.DEBUG,  # Set the default logging level
    format="%(asctime)s - %(levelname)s - %(message)s",  # Customize the log format
    datefmt="%Y-%m-%d %H:%M:%S",  # Format the timestamp
)
logging.getLogger("openai").setLevel(logging.WARNING)  # Show only warnings and errors
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)


class TrainingAgent:

    class EventHandler(AssistantEventHandler):
        def __init__(self, agent):
            super().__init__()
            self.agent = agent
        @override
        def on_event(self, event):
            if self.agent.interrupt_pipe_data:
                return
            self.agent._log({"status": str(event.event)})
            thread_messages = self.agent.client.beta.threads.messages.list(self.agent.thread.id, run_id=event.data.id)
            for message in thread_messages.data:
                self.agent._log({"messages": str(message.content)})
            # Retrieve events that are denoted with 'requires_action'
            # since these will have our tool_calls
            if event.event == 'thread.run.requires_action':
                run_id = event.data.id  # Retrieve the run ID from the event data
                self.handle_requires_action(event.data, run_id)

        def handle_requires_action(self, data, run_id):
            tool_outputs = []
            for tool in data.required_action.submit_tool_outputs.tool_calls:
                self.agent._log({"tool_calls": str(tool)})
                tool_outputs.append({
                    "tool_call_id": tool.id,
                    "output": str(self.agent.function_call_switch[tool.function.name](**json.loads(tool.function.arguments)))
                })
      
            self.agent._log({"tool_outputs": str(tool_outputs)})
            # Submit all tool_outputs at the same time
            self.submit_tool_outputs(tool_outputs, run_id)

        def submit_tool_outputs(self, tool_outputs, run_id):
            # Use the submit_tool_outputs_stream helper
            run = self.agent.client.beta.threads.runs.retrieve(
                thread_id=self.current_run.thread_id, 
                run_id=self.current_run.id
            )
            if run.status != 'expired':
                with self.agent.client.beta.threads.runs.submit_tool_outputs_stream(
                    thread_id=self.current_run.thread_id,
                    run_id=self.current_run.id,
                    tool_outputs=tool_outputs,
                    event_handler=type(self)(self.agent),
                ) as stream:
                    for _ in stream.text_deltas:
                        pass
            else:
                print("run expired!")
                pass



    ASSISTANT_PROMPT = (
        "You are an intelligent agent that has access to a mouse habitat. Inside the habitat, there are two mice, two levers, two mice, a speaker, and a water dispenser.\n"
        "You can control the water dispenser which provides the two mice with access to water. You can control how for how long the mice have access by passing a value in seconds to the feed function \n"
        "You can also create sounds of different frequencies with the speaker. You can do this by passing a frequency to the play_sound function. One lever is on the right side of the cage and the other is on the left side.\n"
        "When a mouse is on the lever, or under it, then the lever is pressed. You have access to a function that informs you when a lever is pressed called wait_for_lever. "
        "When you call this function, the levers are monitored for the specified duration. "
        "If the left lever is pressed by the mouse, the function returns 0; if the right lever is pressed, it returns 1; if neither lever is pressed during that time, the function returns -1.\n"
        "You can wait for the lever to be pressed for up to 2 minutes from a single call but you can call this function multiple times to wait for longer durations.\n"
        # "If you need help you have two ways of getting it. The first is a function called get_reasoning_help, where you can pass in a request as a string, and receive a response from a much smarter artificial intelligence model. "
        "You can call this function once every hour. \n"
        "If you need help you can call a function called get_human_help, where you can pass in a request as a string and receive a response from a human. You can call this function only once every 1 hour it or it will be disabled.\n"
        "Finally you wait for time to pass by passing the number of seconds you would like to wait for into the delay function. The maximum duration is 3 minutes, but you can call this function multiple times to delay for longer durations.\n"
        "Your job is to train the mice to press the lever.\n"
        "You can only exit the program once you are confident that the mice are trained successfully."
    )

    THREAD_PROMPT = (
        "Train the mice to press the lever using the tools that are available to you. "
        "Think upon and execute a strategy that does this, and use the feedback you are getting from the functions to continue to reevaluate and improve that strategy until you feel the mice are successfully trained. "
        "You must be sure that the mice are successfully trained before you can consider this task complete.\n"
    )


    def __init__(self):
        self.lever_status = "idle"
        self.client = OpenAI()
        self.controller = MainController(client=self.client, engine=self)
        self.assistant = self.client.beta.assistants.create(
            instructions=self.ASSISTANT_PROMPT,
            name="Mouse Trainer",
            tools=tools,
            model="gpt-4o",
        )
        self.thread = self.client.beta.threads.create()
        self.message = self.client.beta.threads.messages.create(
            thread_id=self.thread.id,
            role="user",
            content=self.THREAD_PROMPT,
        )

        self.function_call_switch = {
            "feed": self.controller.feed,
            "play_sound": self.controller.play_sound,
            "wait_for_lever": self.controller.wait_for_lever,
            "delay": self.controller.delay,
            "get_human_help": self.controller.get_human_help,
            "get_reasoning_help": self.controller.get_reasoning_help,
        }

        self.log_url = os.getenv("LOG_URL")
        self.api_key = os.getenv("API_KEY")

        logging.info(f"assistant id: {self.assistant.id}")
        logging.info(f"thread id: {self.thread.id}")
        self.interrupt_pipe = "/tmp/interrupt"
        self.interrupt_pipe_data = None
        self._initialize_pipe()
        self.event_handler = self.EventHandler(self)
        self.pipe_thread = threading.Thread(target=self._update_pipe_data, daemon=True)
        self.pipe_thread.start()

    def _initialize_pipe(self):
        if not os.path.exists(self.interrupt_pipe):
            os.mkfifo(self.interrupt_pipe)

    def _update_pipe_data(self):
        while True:
            logging.debug("update pipe data")
            with open(self.interrupt_pipe, 'r') as pipe:
                lines = pipe.readlines()
                if lines:
                    self.interrupt_pipe_data = lines[-1].strip()


    def write_to_pipe(self, data):
        try:
            with open(self.interrupt_pipe, 'w') as pipe:
                pipe.write(data + "\n")
        except Exception as e:
            print(f"Error writing to pipe: {e}")

    def _log(self, data: dict):
        logging.info(data)
        payload = {
            "data": data
        }
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key
        }
        try:
            response = requests.post(self.log_url, json=payload, headers=headers)
        except Exception as e:
            print(f"Error logging data: {e}")


    def train(self):
        if self.interrupt_pipe_data:
            print("*"*10, self.interrupt_pipe_data, "*"*10)
            logging.info(self.interrupt_pipe_data)
            self.client.beta.threads.messages.create(
                thread_id=self.thread.id,
                role="user",
                content=self.interrupt_pipe_data
            )
        self.interrupt_pipe_data = None
        with self.client.beta.threads.runs.stream(
            thread_id=self.thread.id,
            assistant_id=self.assistant.id,
            event_handler=self.EventHandler(self)
        ) as stream:
            for text in stream.text_deltas:
                if self.interrupt_pipe_data:
                    break

    def reset(self):
        runs = self.client.beta.threads.runs.list(
            thread_id=self.thread.id
        )
        for run in runs.data:
            if run.status == "queued" or run.status == "in_progress" or run.status == "requires_action":
                try:
                    self.client.beta.threads.runs.cancel(
                        thread_id=self.thread.id,
                        run_id=run.id
                    )
                except Exception as e:
                    print(f"Error cancelling run: {e}")
                check = self.client.beta.threads.runs.retrieve(
                    thread_id=self.thread.id,
                    run_id=run.id
                )
                while check.status == "cancelling":
                    check = self.client.beta.threads.runs.retrieve(
                        thread_id=self.thread.id,
                        run_id=run.id
                    )
                    time.sleep(0.1)

    def cleanup(self):
        os.remove(self.interrupt_pipe)
        self.controller.cleanup()
