
import RPi.GPIO as GPIO
import time
from enum import Enum
from openai import OpenAI
import threading

class MainController:

    HUMAN_TIMEOUT = 60*60 # 1 hour
    REASONING_TIMEOUT = 60*60 # 1 hour

    LEFT_LEVER_LED = 8
    RIGHT_LEVER_LED = 1
    LEFT_LEVER_SWITCH = 26
    RIGHT_LEVER_SWITCH = 20

    MIN_FREQ = 50
    MAX_FREQ = 10000

    class LeverState(Enum):
        UNPRESSED = 0
        PRESSED = 1

    def __init__(self, client: OpenAI=None, engine=None):
        GPIO.setmode(GPIO.BCM)

        GPIO.setup(self.LEFT_LEVER_LED, GPIO.OUT)
        GPIO.output(self.LEFT_LEVER_LED, GPIO.LOW)
        GPIO.setup(self.RIGHT_LEVER_LED, GPIO.OUT)
        GPIO.output(self.RIGHT_LEVER_LED, GPIO.LOW)

        GPIO.setup(self.LEFT_LEVER_SWITCH, GPIO.IN, pull_up_down=GPIO.PUD_UP) 
        GPIO.setup(self.RIGHT_LEVER_SWITCH, GPIO.IN, pull_up_down=GPIO.PUD_UP) 
        GPIO.add_event_detect(self.LEFT_LEVER_SWITCH, GPIO.FALLING, callback=self._left_lever_callback, bouncetime=300)
        GPIO.add_event_detect(self.RIGHT_LEVER_SWITCH, GPIO.FALLING, callback=self._right_lever_callback, bouncetime=300)

        self.engine = engine
        self.client = client
        self.feeder = Feeder()
        self.speaker = Speaker()
        self.lever_state = [
            self.LeverState.UNPRESSED, # left lever
            self.LeverState.UNPRESSED, # right lever
        ]
        self._last_human_help = 0
        self._last_reasoning_help = 0

    def _left_lever_callback(self, channel):
        self.engine.status = "left pressed"
        self.lever_state[0] = self.LeverState.PRESSED
        GPIO.output(self.LEFT_LEVER_LED, GPIO.HIGH)
        threading.Timer(3, GPIO.output, args=(self.LEFT_LEVER_LED, GPIO.LOW)).start()
        
    def _right_lever_callback(self, channel):
        self.engine.status = "right pressed"
        self.lever_state[1] = self.LeverState.PRESSED
        GPIO.output(self.RIGHT_LEVER_LED, GPIO.HIGH)
        threading.Timer(3, GPIO.output, args=(self.RIGHT_LEVER_LED, GPIO.LOW)).start()

    def feed(self, duration: int) -> bool:
        return self.feeder.feed(duration)

    def play_sound(self, duration: int, frequency: int) -> bool:
        if frequency < self.MIN_FREQ or frequency > self.MAX_FREQ:
            return False
        return self.speaker.play(duration, frequency)

    def wait_for_lever(self, duration: int) -> int:
        self.engine.lever_status = "waiting"
        self.lever_state[0] = self.LeverState.UNPRESSED
        self.lever_state[1] = self.LeverState.UNPRESSED
        start_time = time.time()
        while (time.time() - start_time < duration) and \
        (self.lever_state[0] == self.LeverState.UNPRESSED) and \
        (self.lever_state[1] == self.LeverState.UNPRESSED):
            time.sleep(0.1)
        if self.lever_state[0] == self.LeverState.PRESSED:
            return 0 # left lever   
        elif self.lever_state[1] == self.LeverState.PRESSED:
            return 1 # right lever
        return -1 # neither lever

    def delay(self, duration: int) -> bool:
        time.sleep(duration)
        return True

    def get_human_help(self, request: str) -> str:
        if time.time() - self._last_human_help >= self.HUMAN_TIMEOUT:
            self._last_human_help = time.time()
            return str(input(request + ":\n\n"))
        return (
            "You can only use the get_human_help function once every 24 hours.\n"
            "You last used it " + str(time.time() - self._last_human_help) + " seconds ago.\n"
            "Please wait " + str(self.HUMAN_TIMEOUT - (time.time() - self._last_human_help)) + " seconds before using it again.\n"
        )
    
    # def get_reasoning_help(self, request: str) -> str:
    #     self._last_reasoning_help = time.time()
    #     prompt = (
    #         "You are a helpful assistant that helps another smaller LLM with complex reasoning tasks.\n"
    #         "The smaller LLM is working on a complex task where it has to control the location of two mice in its cage using the tools provided.\n"
    #         "The LLM has access to the following tools:\n"
    #         "1. feed(duration: int) -> bool: Feeds the mouse for the given duration in seconds.\n"
    #         "2. lights(duration: int, quadrant: int) -> bool: Turns on the lights for the given duration in seconds. The quadrant is an integer between 0 and 3, representing which quadrant of the cage the mouse is in.\n"
    #         "3. speakers(duration: int, quadrant: int) -> bool: Plays a sound for the given duration in seconds. The quadrant is an integer between 0 and 3, representing which quadrant of the cage the mouse is in.\n"
    #         "4. get_mouse_position() -> Tuple[int, int]: Returns the positions of the two mice in the cage as a tuple of two integers, representing which quadrant of the cage each mouse is in. If the mouse is buried or not visible it will return -1 for that mouse's position. The order of the mice is not preserved.\n"
    #         "5. get_human_help(request: str) -> str: Returns a response to the given request. Use only when you are stuck. This tool can be used at most once every 24 hours or it will be disabled.\n\n"
    #         "The smaller LLM is having a hard time refining its strategy to train the mouse to go to a certain quadrant of the cage.\n"
    #         "You need to reference scientific studies on how scientists have trained mice using rewards to come up with a strategy for the smaller LLM to use.\n"
    #         "You should give the smaller LLM a complete strategy that works with the tools provided and doesn't require any additional tools.\n"
    #         "You don't need to give step by step instructions, just the overall strategy, but be as detailed as possible and root your reasoning in scientific studies that are well established for training mice.\n"
    #         "You can only be used once every hour, so make sure your response is complete and doesn't require addtional clarification from the smaller LLM.\n"
    #         "Here is the request / status from the smaller LLM: \n\n"
    #         + request + "\n\n"
    #     )

    #     if time.time() - self._last_reasoning_help >= self.REASONING_TIMEOUT:
    #         return self.client.chat.completions.create(
    #             model="o1-preview",
    #             messages=[
    #                 {
    #                     "role": "user", 
    #                     "content": prompt
    #                 }
    #             ]
    #         )

    #     return (
    #         "You can only use the get_reasoning_help function once every hour.\n"
    #         "You last used it " + str(time.time() - self._last_reasoning_help) + " seconds ago.\n"
    #         "Please wait " + str(self.REASONING_TIMEOUT - (time.time() - self._last_reasoning_help)) + " seconds before using it again.\n"
    #     )
    
    def cleanup(self):
        GPIO.output(self.LEFT_LEVER_LED, GPIO.LOW)
        GPIO.output(self.RIGHT_LEVER_LED, GPIO.LOW)
        self.feeder.cleanup()
        self.speaker.cleanup()


class Feeder:

    class State(Enum):
        IDLE = 0
        FEEDING = 1

    class Direction(Enum):
        LOWER_FEED = 0
        LIFT_FEED = 1
       

    # GPIO pins
    PINS = [17, 18, 27, 22]
    SWITCH_PIN = 16

    # Stepper motor step sequence
    STEP_SEQUENCE = [
        [1,0,0,0],
        [0,1,0,0],
        [0,0,1,0],
        [0,0,0,1]
    ]

    LIFT_STEPS = 200

    def __init__(self):
        GPIO.setmode(GPIO.BCM)
        self._setup_gpio()

        input("Verify feeder is lifted and press enter to continue...")
        if GPIO.input(self.SWITCH_PIN) != GPIO.HIGH:
            raise Exception("Feeder is not lifted")
        self.state = self.State.IDLE

    def _setup_gpio(self):
        for p in self.PINS:
            GPIO.setup(p, GPIO.OUT)
            GPIO.output(p, False)
        GPIO.setup(self.SWITCH_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Pull-up enabled

    def _step(self, direction: Direction):
        
        # (TODO) this is a stub, it may be reversed -- need to check hardware setup
        step_sequence = self.STEP_SEQUENCE if direction == self.Direction.LOWER_FEED else list(reversed(self.STEP_SEQUENCE))
        for step in step_sequence:
            for pin, val in zip(self.PINS, step):
                GPIO.output(pin, val)
            time.sleep(0.01)

    def _lower_feeder(self):
        while GPIO.input(self.SWITCH_PIN) == GPIO.HIGH:
            self._step(self.Direction.LOWER_FEED)

    def _raise_feeder(self):
        while GPIO.input(self.SWITCH_PIN) == GPIO.LOW:
            self._step(self.Direction.LIFT_FEED)
        for _ in range(self.LIFT_STEPS):
            self._step(self.Direction.LIFT_FEED)

    def cleanup(self):
        while self.state == self.State.FEEDING:
            time.sleep(0.1)
        # GPIO.cleanup()

    def feed(self, duration: int) -> bool:
        try:
            if self.state == self.State.IDLE:
                self.state = self.State.FEEDING
                self._lower_feeder()
                time.sleep(duration)
                self._raise_feeder()
                self.state = self.State.IDLE
                return True
            else:
                return False
        except Exception as e:
            return False

class Speaker:

    SPEAKER_PIN = 21
    SPEAKER_LED = 7

    def __init__(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.SPEAKER_PIN, GPIO.OUT)
        GPIO.setup(self.SPEAKER_LED, GPIO.OUT)
        GPIO.output(self.SPEAKER_LED, GPIO.LOW)

    def play(self, duration: int, frequency: int) -> bool:
        try:
            GPIO.output(self.SPEAKER_LED, GPIO.HIGH)
            pwm = GPIO.PWM(self.SPEAKER_PIN, frequency)
            pwm.start(50)
            time.sleep(duration)
            pwm.stop()
            GPIO.output(self.SPEAKER_LED, GPIO.LOW)
            return True
        except Exception as e:
            print(e)
            return False

    def cleanup(self):
        GPIO.output(self.SPEAKER_LED, GPIO.LOW)
        # GPIO.cleanup()
