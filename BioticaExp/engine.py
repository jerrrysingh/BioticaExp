
from controller import MainController
from openai import OpenAI
from tools import tools

import requests

import time
from datetime import datetime
import json
import os
import logging

from dotenv import load_dotenv

load_dotenv()

# Configure the logger
logging.basicConfig(
    filename='agent.log',
    level=logging.INFO,  # Set the default logging level
    format="%(asctime)s - %(levelname)s - %(message)s",  # Customize the log format
    datefmt="%Y-%m-%d %H:%M:%S",  # Format the timestamp
)
logging.getLogger("openai").setLevel(logging.WARNING)  # Show only warnings and errors
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)


class TrainingAgent:

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
        "If you need help you can call a function called get_human_help, where you can pass in a request as a string and receive a response from a human. You can call this function only once every 1 hour it or itwill be disabled.\n"
        # "Finally you wait for time to pass by passing the number of seconds you would like to wait for into the delay function. The maximum duration is 5 minutes, but you can call this function multiple times to delay for longer durations.\n"
        "Your job is to train the mice to press the lever."
    )

    THREAD_PROMPT = (
        "Train the mice to press the lever using the tools that are available to you. "
        "Think upon and execute a strategy that does this, and use the feedback you are getting from the functions to continue to reevaluate and improve that strategy until you feel the mice are successfully trained. "
        "You must be sure that the mice are successfully trained before you can consider this task complete.\n"
    )


    def __init__(self):
        self.status = "idle"
        self.lever_status = "idle"
        self.client = OpenAI()
        self.controller = MainController(engine=self)
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
            # "delay": self.controller.delay,
            "get_human_help": self.controller.get_human_help,
            # 'get_reasoning_help': self.controller.get_reasoning_help,
        }

        self.log_url = os.getenv("LOG_URL")
        self.api_key = os.getenv("API_KEY")

        logging.info(f"assistant id: {self.assistant.id}")
        logging.info(f"thread id: {self.thread.id}")

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


    def train(self, additional_instructions: str=None):
        logging.info(additional_instructions)
        run = self.client.beta.threads.runs.create(
            thread_id=self.thread.id,
            assistant_id=self.assistant.id,
            additional_instructions=additional_instructions
        )
        self.status = "running"

        while run.status == "queued" or run.status == "in_progress":
            run = self.client.beta.threads.runs.retrieve(
                thread_id=self.thread.id,
                run_id=run.id
            )
            if self.status == "kill" or (self.status != "waiting" and "pressed" in self.status):
                try:
                    run = self.client.beta.threads.runs.cancel(
                        thread_id=self.thread.id,
                        run_id=run.id
                    )
                    logging.info("Run cancelled")
                except Exception as e:
                    self.status = "error"
                    print(f"Error cancelling run: {e}")
                return self.status
            time.sleep(0.5)

        while run.status != "completed":
            if self.status == "kill" or (self.status != "waiting" and "pressed" in self.status):
                return self.status
            self._log({"status": run.status})
            thread_messages = self.client.beta.threads.messages.list(self.thread.id, run_id=run.id)
            for message in thread_messages.data:
                self._log({"messages": str(message.content)})

            tool_outputs = []
            for tool in run.required_action.submit_tool_outputs.tool_calls:
                self._log({"tool_calls": str(tool)})
                try:
                    tool_outputs.append({
                        "tool_call_id": tool.id,
                        "output": str(self.function_call_switch[tool.function.name](**json.loads(tool.function.arguments)))
                    })
                except Exception as e:
                    print(f"Error calling function {tool.function.name}: {e}")
            logging.info(tool_outputs)
            time.sleep(3)
            try:
                # if run.status != "expired":
                run = self.client.beta.threads.runs.submit_tool_outputs(
                    thread_id=self.thread.id,
                    run_id=run.id,
                    tool_outputs=tool_outputs
                )
                while run.status == "queued" or run.status == "in_progress":
                    run = self.client.beta.threads.runs.retrieve(
                        thread_id=self.thread.id,
                        run_id=run.id
                    )
                    if self.status == "kill" or (self.status != "waiting" and "pressed" in self.status):
                        try:
                            run = self.client.beta.threads.runs.cancel(
                                thread_id=self.thread.id,
                                run_id=run.id
                            )
                            logging.info("Run cancelled")
                        except Exception as e:
                            self.status = "error"
                            print(f"Error cancelling run: {e}")                            
                        return self.status
                    time.sleep(0.5)
                logging.info("Tool outputs submitted successfully.")
                # else:
                #     print("Run expired")
            except Exception as e:
                print("Failed to submit tool outputs:", e)

    def cleanup(self):
        self.controller.cleanup()

# from openai import OpenAI
# client = OpenAI()

# my_assistant = client.beta.assistants.create(
#     instructions="You are a personal math tutor. When asked a question, write and run Python code to answer the question.",
#     name="Math Tutor",
#     tools=[{"type": "code_interpreter"}],
#     model="gpt-4o",
# )
# print(my_assistant)
