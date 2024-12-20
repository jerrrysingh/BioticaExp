# main.py
from engine import TrainingAgent
import threading
import queue
import time

def get_additional_instructions(input_queue, stop_event):
    if not stop_event.is_set():
        user_input = input("Enter additional instructions: ")
        input_queue.put(user_input)
        stop_event.set()

def train_agent(agent, additional_instructions, result_queue):
    result_queue.put(agent.train(additional_instructions))

def main():
    agent = TrainingAgent()

    print(f"assistant id: {agent.assistant.id}")
    print(f"thread id: {agent.thread.id}")

    additional_instructions = None

    try:
        for i in range(100):
            print("*"*10, i, "*"*10)
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
                time.sleep(1)
            agent.status = "kill"
            train_thread.join()
            print("Agent killed, restarting...\n")
            runs = agent.client.beta.threads.runs.list(
                thread_id=agent.thread.id
            )
            for run in runs.data:
                if run.status == "queued" or run.status == "in_progress" or run.status == "requires_action":
                    try:
                        agent.client.beta.threads.runs.cancel(
                            thread_id=agent.thread.id,
                            run_id=run.id
                        )
                    except Exception as e:
                        print(f"Error cancelling run: {e}")
                check = agent.client.beta.threads.runs.retrieve(
                    thread_id=agent.thread.id,
                    run_id=run.id
                )
                while check.status == "cancelling":
                    check = agent.client.beta.threads.runs.retrieve(
                        thread_id=agent.thread.id,
                        run_id=run.id
                    )
                    time.sleep(0.1)
            agent.cleanup()
            if not result_queue.empty():
                train_result = result_queue.get()
                print(f"train result: {train_result}")
                if train_result and "pressed" in train_result:
                    additional_instructions = f"The mouse recentlly pressed the {train_result}!"

            time.sleep(3)
    finally:
        print("Cleaning up...")
        agent.cleanup()

if __name__ == "__main__":
    main()
