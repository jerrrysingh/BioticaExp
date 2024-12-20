# main.py
from engine import TrainingAgent
import threading
import queue
import time

def main():
    agent = TrainingAgent()

    print(f"assistant id: {agent.assistant.id}")
    print(f"thread id: {agent.thread.id}")

    i = 0
    try:
        while True:
            print("*"*10, i, "*"*10)
            i += 1
            agent.train()
            print("Agent killed, restarting...\n")
            agent.reset()
            time.sleep(3)
    finally:
        print("Cleaning up...")
        agent.cleanup()

if __name__ == "__main__":
    main()
