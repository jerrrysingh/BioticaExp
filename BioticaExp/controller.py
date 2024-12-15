
import RPi.GPIO as GPIO
import time
from enum import Enum


class MainController:
    def __init__(self):
        self.feeder = Feeder()
        self.lights = Lights()
        self.speakers = Speakers()

    def feed(self, duration: int) -> bool:
        return self.feeder.feed(duration)
    
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
