import multiprocessing
import multiprocessing.managers
from pathlib import Path
import signal
import sys
import time
from threading import Lock, Event
import logging
import json

action_lock = Lock()
shutdown_event = Event()
is_locked = multiprocessing.Value('b', False)  # Shared boolean flag for lock state

def get_action(job_id=None, index=0):
    """
    Get an action from the actions list.
    
    Args:
        job_id (str, optional): Identifier for the job requesting the action
        index (int, optional): Index of the action to retrieve (default=0 for first action)
    
    Returns:
        dict or None: The requested action if available, None otherwise
    """
    with action_lock:
        # Check if system is locked
        if is_locked.value:
            job_str = f" by job {job_id}" if job_id else ""
            logging.info(f"Action requested{job_str} but system is locked")
            return None
            
        with open(f"{log_dir}/actions.json", "r") as fr:
            actions = json.load(fr)
            print(actions)

        if actions and 0 <= index < len(actions):
            # Remove and return the action at the specified index
            action = actions.pop(index)
            job_str = f" to job {job_id}" if job_id else ""
            logging.info(f"Action {action['cmd']} at index {index} assigned{job_str}")
            with open(f"{log_dir}/actions.json", "w+") as fw:
                json.dump(actions, fw, indent=4)
            return action
        return None
    
def add_action(action):
    with action_lock:
        if not Path(f'{log_dir}/actions.json').exists():
            with open(f"{log_dir}/actions.json", "w+") as f:
                json.dump([], f)

        with open(f"{log_dir}/actions.json", "r") as f:
            actions = json.load(f)

        actions.append(action)

        with open(f"{log_dir}/actions.json", "w") as f:
            json.dump(actions, f, indent=4)
        logging.info(f"Action {action['cmd']} added.")

def status():
    with action_lock:
        with open(f"{log_dir}/actions.json", "r") as f:
            actions = json.load(f)
            return actions

def lock():
    """Lock the manager to prevent it from providing new actions."""
    with action_lock:
        is_locked.value = True
        logging.info("Manager locked - no new actions will be provided")
    return True

def unlock():
    """Unlock the manager to allow it to provide actions again."""
    with action_lock:
        is_locked.value = False
        logging.info("Manager unlocked - actions can now be provided")
    return True

def stop():
    logging.info('Stop command received')
    shutdown_event.set()
    return True  # Return value to prevent client from hanging

class MyManager(multiprocessing.managers.BaseManager):
    pass

def signal_handler(signum, frame):
    logging.info(f'Received signal {signum}')
    shutdown_event.set()

import argparse
def main():
    global log_dir

    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=50000, help="Port to bind to")
    parser.add_argument("--log-dir", type=str, default=(Path().home() / '.bulb').as_posix(), help="Port to bind to")

    args = parser.parse_args()

    log_dir = args.log_dir
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    if not Path(f"{log_dir}/actions.json").exists():
        with open(f"{log_dir}/actions.json", "w+") as f:
            json.dump([], f)

    # Configure logging to log to both file and terminal with timestamps
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
    file_handler = logging.FileHandler(f'{log_dir}/jobs.log')
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
    logging.getLogger().addHandler(file_handler)

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    MyManager.register("get_action", get_action)
    MyManager.register("add_action", add_action)
    MyManager.register("status", status)
    MyManager.register("stop", stop)
    MyManager.register("lock", lock)
    MyManager.register("unlock", unlock)
    
    manager = MyManager(address=("0.0.0.0", args.port), authkey=b"abc")
    server = manager.get_server()
    print("Manager is running;")
    print(f"Server address: {server.address}")
    print("Press Ctrl+C to exit.")

    # Run the server in a separate thread
    import threading
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()

    # Wait for shutdown event
    try:
        while not shutdown_event.is_set():
            time.sleep(0.1)
    except KeyboardInterrupt:
        logging.info("Keyboard interrupt received")
    finally:
        logging.info("Shutting down manager...")
        server.stop_event.set()
        server_thread.join(timeout=5)
        logging.info("Manager shutdown complete")
        sys.exit(0)

if __name__ == "__main__":
    main()