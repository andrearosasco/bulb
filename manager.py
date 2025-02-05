
import multiprocessing
import multiprocessing.managers
from pathlib import Path
import time
from threading import Lock
import logging
import json

# Configure logging to log to both file and terminal with timestamps
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
file_handler = logging.FileHandler('jobs.log')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
logging.getLogger().addHandler(file_handler)

action_lock = Lock()


def get_action(job_id):
    with action_lock:
        with open("actions.json", "r") as fr:
            actions = json.load(fr)
            print(actions)

        if actions:
            action = actions.pop(0)
            logging.info(f"Action {action['cmd']} assigned to job {job_id}")
            with open("actions.json", "w+") as fw:
                json.dump(actions, fw)
            return action
        return None
    
def add_action(action):
    with action_lock:
        if not Path('actions.json').exists():
            with open("actions.json", "w+") as f:
                json.dump([], f)

        with open("actions.json", "r") as f:
            actions = json.load(f)

        actions.append(action)

        with open("actions.json", "w") as f:
            json.dump(actions, f, indent=4)
        logging.info(f"Action {action['cmd']} added.")

class MyManager(multiprocessing.managers.BaseManager):
    pass

# jobber                                                                                                                                                                                                                                                        app.add_typer(defaults.app, name="defaults")                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                @app.command()
def main():
    MyManager.register("get_action", get_action)
    MyManager.register("add_action", add_action)
    manager = MyManager(address=("0.0.0.0", 50000), authkey=b"abc")
    server = manager.get_server()
    print("Manager is running; press Ctrl+C to exit.")
    server.serve_forever()

if __name__ == "__main__":
    main()