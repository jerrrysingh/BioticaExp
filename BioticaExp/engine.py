
from controller import MainController
from openai import OpenAI
class TrainingAgent:
    def __init__(self):
        self.controller = MainController()
        self.client = OpenAI()

    def train(self):
        pass

    def cleanup(self):
        self.controller.cleanup()
