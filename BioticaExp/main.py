# main.py
from engine import TrainingAgent
import threading
import queue
import time



def train_agent(agent, additional_instructions, result_queue):
    result_queue.put(agent.train(additional_instructions))

if __name__ == "__main__":
    agent = TrainingAgent()
    result_queue = queue.Queue()
    print(f"assistant id: {agent.assistant.id}")
    print(f"thread id: {agent.thread.id}")

    additional_instructions = None

    while True:
        agent.status = "idle"
        train_thread = threading.Thread(target=train_agent, args=(agent, additional_instructions, result_queue))
        train_thread.start()
        # additional_instructions = input("Enter additional instructions: ")
        agent.status = "kill"
        train_thread.join()
        print("Agent killed, restarting...\n")
        agent.cleanup()
        if not result_queue.empty():
            train_result = result_queue.get()
            print(f"train result: {train_result}")
            # if "pressed" in train_result:
            #     additional_instructions = f"The mouse recentlly pressed the {train_result}"
        time.sleep(10)