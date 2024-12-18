# main.py
from engine import TrainingAgent
import threading
import queue
import time

def get_additional_instructions(input_queue, stop_event):
    if not stop_event.is_set():
        user_input = input("Enter additional instructions:")
        input_queue.put(user_input)
        stop_event.set()

def train_agent(agent, additional_instructions, result_queue):
    result_queue.put(agent.train(additional_instructions))

if __name__ == "__main__":
    agent = TrainingAgent()

    print(f"assistant id: {agent.assistant.id}")
    print(f"thread id: {agent.thread.id}")

    additional_instructions = None

    while True:
        input_queue = queue.Queue()
        input_stop_event = threading.Event()
        input_thread = threading.Thread(target=get_additional_instructions, args=(input_queue, input_stop_event), daemon=True)
        input_thread.start()

        result_queue = queue.Queue()
        agent.status = "idle"
        train_thread = threading.Thread(target=train_agent, args=(agent, additional_instructions, result_queue))
        train_thread.start()
        # Monitor the training thread and check for input
        while train_thread.is_alive():
            if input_stop_event.is_set() and not input_queue.empty():
                additional_instructions = input_queue.get()
                print(f"Received additional instructions: {additional_instructions}")
                agent.status = "kill"
            time.sleep(1)

        train_thread.join()
        print("Agent killed, restarting...\n")
        agent.cleanup()
        if not result_queue.empty():
            train_result = result_queue.get()
            print(f"train result: {train_result}")
            if "pressed" in train_result:
                additional_instructions = f"The mouse recentlly pressed the {train_result}!"

        time.sleep(10)