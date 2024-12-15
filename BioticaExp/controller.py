
import RPi.GPIO as GPIO
import time
from enum import Enum
from openai import OpenAI
from typing import Tuple

class MainController:

    HUMAN_TIMEOUT = 60*60*24 # 1 day
    REASONING_TIMEOUT = 60*60 # 1 hour

    def __init__(self, client: OpenAI):
        self.client = client
        self.feeder = Feeder()
        self.lights = Lights()
        self.speakers = Speakers()
        self._last_human_help = time.time()
        self._last_reasoning_help = time.time()

    def _init_camera(self):
        pass
        
    def feed(self, duration: int) -> bool:
        return self.feeder.feed(duration)
    
    def get_mouse_position(self) -> Tuple[int, int]:
        pass

    def get_human_help(self, request: str) -> str:
        if time.time() - self._last_human_help >= self.HUMAN_TIMEOUT:
            return input(request + ":\n\n")
        return (
            "You can only use the get_human_help function once every 24 hours.\n"
            "You last used it " + str(time.time() - self._last_human_help) + " seconds ago.\n"
            "Please wait " + str(self.HUMAN_TIMEOUT - (time.time() - self._last_human_help)) + " seconds before using it again.\n"
        )
    
    def get_reasoning_help(self, request: str) -> str:

        prompt = (
            "You are a helpful assistant that helps another smaller LLM with complex reasoning tasks.\n"
            "The smaller LLM is working on a complex task where it has to control the location of two mice in its cage using the tools provided.\n"
            "The LLM has access to the following tools:\n"
            "1. feed(duration: int) -> bool: Feeds the mouse for the given duration in seconds.\n"
            "2. lights(duration: int) -> bool: Turns on the lights for the given duration in seconds.\n"
            "3. speakers(duration: int) -> bool: Plays a sound for the given duration in seconds.\n"
            "4. get_mouse_position() -> Tuple[int, int]: Returns the positions of the two mice in the cage as a tuple of two integers, representing which quadrant of the cage each mouse is in. If the mouse is buried or not visible it will return -1 for that mouse's position. The order of the mice is not preserved.\n"
            "5. get_human_help(request: str) -> str: Returns a response to the given request. Use only when you are stuck. This tool can be used at most once every 24 hours or it will be disabled.\n\n"
            "The smaller LLM is having a hard time refining its strategy to train the mouse to go to a certain quadrant of the cage.\n"
            "You need to reference scientific studies on how scientists have trained mice using rewards to come up with a strategy for the smaller LLM to use.\n"
            "You should give the smaller LLM a complete strategy that works with the tools provided and doesn't require any additional tools.\n"
            "You don't need to give step by step instructions, just the overall strategy, but be as detailed as possible and root your reasoning in scientific studies that are well established for training mice.\n"
            "You can only be used once every hour, so make sure your response is complete and doesn't require addtional clarification from the smaller LLM.\n"
            "Here is the request / status from the smaller LLM: \n\n"
            + request + "\n\n"
        )

        if time.time() - self._last_reasoning_help >= self.REASONING_TIMEOUT:
            return self.client.chat.completions.create(
                model="o1-preview",
                messages=[{"role": "user", "content": prompt}],
            )
        return (
            "You can only use the get_reasoning_help function once every hour.\n"
            "You last used it " + str(time.time() - self._last_reasoning_help) + " seconds ago.\n"
            "Please wait " + str(self.REASONING_TIMEOUT - (time.time() - self._last_reasoning_help)) + " seconds before using it again.\n"
        )
    
    def cleanup(self):
        self.feeder.cleanup()
        self.lights.cleanup()
        self.speakers.cleanup()


class Feeder:

    class State(Enum):
        IDLE = 0
        FEEDING = 1

    class Direction(Enum):
        LIFT_FEED = 0
        FEED = 1

    # GPIO pins
    IN1 = 17
    IN2 = 18
    IN3 = 27
    IN4 = 22

    # Stepper motor step sequence
    STEP_SEQUENCE = [
        [1, 0, 0, 0],
        [1, 1, 0, 0],
        [0, 1, 0, 0],
        [0, 1, 1, 0],
        [0, 0, 1, 0],
        [0, 0, 1, 1],
        [0, 0, 0, 1],
        [1, 0, 0, 1],
    ]

    STEPS_PER_FEED = 512

    def __init__(self):
        GPIO.setmode(GPIO.BCM)
        self._setup_gpio()

        # (TODO) this requires manual checking of state before initializing - should  prompt user instead

        self.state = Feeder.State.Idle

    def _setup_gpio(self):
        GPIO.setup(self.IN1, GPIO.OUT)
        GPIO.setup(self.IN2, GPIO.OUT)
        GPIO.setup(self.IN3, GPIO.OUT)
        GPIO.setup(self.IN4, GPIO.OUT)

    def _step(self, num_steps: int, direction: Direction):
        
        # (TODO) this is a stub, it may be reversed -- need to check hardware setup
        step_sequence = Feeder.STEP_SEQUENCE if direction == Feeder.Direction.LIFT_FEED else reversed(Feeder.STEP_SEQUENCE)
        for _ in range(num_steps):
            for step in step_sequence:
                GPIO.output(self.IN1, step[0])
                GPIO.output(self.IN2, step[1])
                GPIO.output(self.IN3, step[2])
                GPIO.output(self.IN4, step[3])
                time.sleep(0.001)

    def _lower_feeder(self):
        self._step(Feeder.STEPS_PER_FEED, Feeder.Direction.FEED)

    def _raise_feeder(self):
        self._step(Feeder.STEPS_PER_FEED, Feeder.Direction.LIFT_FEED)

    def cleanup(self):
        GPIO.cleanup()

    def feed(self, duration: int) -> bool:
        if self.state == Feeder.State.Idle:
            self.state = Feeder.State.Feeding
            self._lower_feeder()
            time.sleep(duration)
            self._raise_feeder()
            self.state = Feeder.State.Idle
            return True
        
        # (TODO) add better error handling
        return False # should be unreachable unless error

class Lights:
    def __init__(self):
        pass

    def cleanup(self):
        pass


class Speakers:
    def __init__(self):
        pass

    def cleanup(self):
        pass

