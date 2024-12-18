
from controller import MainController
from openai import OpenAI
from tools import tools

import time
import json
from dotenv import load_dotenv

load_dotenv()



class TrainingAgent:

    ASSISTANT_PROMPT = (
        "You are an intelligent agent that has access to a mouse habitat. Inside the habitat, there are two mice, two levers, two mice, a speaker, and a water dispenser.\n"
        "You can control the water dispenser which provides the two mice with access to water. You can control how for how long the mice have access by passing a value in seconds to the feed function \n"
        "You can also create sounds of different frequencies with the speaker. You can do this by passing a frequency to the play_sound function. One lever is on the right side of the cage and the other is on the left side.\n"
        "When a mouse is on the lever, or under it, then the lever is pressed. You have access to a function that informs you when a lever is pressed called wait_for_lever. "
        "When you call this function, the levers are monitored for the next 3 minutes. "
        "If the left lever is pressed by the mouse, the function returns 0; if the right lever is pressed, it returns 1; if neither lever is pressed during that time, the function returns -1.\n"
        # "If you need help you have two ways of getting it. The first is a function called get_reasoning_help, where you can pass in a request as a string, and receive a response from a much smarter artificial intelligence model. "
        "You can call this function once every hour. \n"
        "If you need help you can call a function called get_human_help, where you can pass in a request as a string and receive a response from a human. You can call this function only once every 24 hours or it will be disabled.\n"
        "Finally you wait for time to pass by passing the number of seconds you would like to wait for into the delay function. \n"
        "Your job is to train the mice to press the lever."
    )

    THREAD_PROMPT = (
        "Train the mice to press the lever using the tools that are available to you. "
        "Think upon and execute a strategy that does this, and use the feedback you are getting from the functions to continue to reevaluate and improve that strategy until you feel the mice are successfully trained. "
        "You must be sure that the mice are successfully trained before you can consider this task complete.\n"
    )


    def __init__(self):
        self.client = OpenAI()
        self.controller = MainController()
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
            # 'get_reasoning_help': self.controller.get_reasoning_help,
        }

    def train(self):
        run = self.client.beta.threads.runs.create_and_poll(
            thread_id=self.thread.id,
            assistant_id=self.assistant.id,
        )
        print(run.status)
        while run.status != "completed":
            tool_outputs = []
            print(run.required_action.submit_tool_outputs.tool_calls)
            for tool in run.required_action.submit_tool_outputs.tool_calls:
                try:
                    tool_outputs.append({
                        "tool_call_id": tool.id,
                        "output": str(self.function_call_switch[tool.function.name](**json.loads(tool.function.arguments)))
                    })
                except Exception as e:
                    print(f"Error calling function {tool.function.name}: {e}")
            print(tool_outputs)
            time.sleep(3)
            try:
                run = self.client.beta.threads.runs.submit_tool_outputs_and_poll(
                    thread_id=self.thread.id,
                    run_id=run.id,
                    tool_outputs=tool_outputs
                )
                print("Tool outputs submitted successfully.")
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
