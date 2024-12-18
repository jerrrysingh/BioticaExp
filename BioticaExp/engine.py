
from controller import MainController
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class TrainingAgent:
    def __init__(self):
        self.client = OpenAI()
        self.controller = MainController(client=self.client)
        self.assistant = self.client.beta.assistants.create(
            instructions="You are a personal math tutor. When asked a question, write and run Python code to answer the question.",
            name="Mouse Trainer",
            tools=[
                {
                    "type": "function",
                    "function": {
                        "name": "feed",
                        "description": "Lowers the mouse water bottle for a specified duration.",
                        "strict": true,
                        "parameters": {
                            "type": "object",
                            "required": [
                                "duration"
                            ],
                            "properties": {
                                "duration": {
                                    "type": "number",
                                    "description": "The duration to lower the mouse water bottle in seconds"
                                }
                            },
                            "additionalProperties": false
                        }
                    }
                }
            ],
            model="gpt-4o",
        )

    def train(self):
        pass

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
