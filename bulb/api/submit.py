import os
import subprocess
import tempfile
import datetime
from pathlib import Path
import atexit
import uuid
import multiprocessing.managers
import json

from bulb.utils.git import commit_to_ref, push_ref, run_git_command
from bulb.utils.misc import get_manager_address, get_user_config
    

# Function to set up directories and save git info
def log_info(log_dir, action, name, action_id):
    Path(log_dir).mkdir(parents=True, exist_ok=True)

    exp_commit = subprocess.check_output(['git', 'rev-parse', 'HEAD']).strip().decode()
    git_diff = subprocess.check_output(['git', 'diff', 'HEAD']).decode()
    
    # Try to load existing data first
    info = {}
    if os.path.exists(f"{log_dir}/info.json"):
        with open(f"{log_dir}/info.json", 'r') as f:
            info = json.load(f)
    
    # Update with new data
    info.update({
        'action_id': action_id,
        'commit': exp_commit,
        'action': action,
        'name': name,
        'status': 'Scheduled',
        'submission_time': datetime.datetime.now().strftime("%Y%m%d_%H%M%S"),
    })
    
    with open(f"{log_dir}/meta.json", 'w+') as f:
        json.dump(info, f, indent=2)


# Function to save the run script
def push_project(action_id, link_dirs=[]):

        ref_name = f"refs/bulb/{action_id}"
        commit_message = "Bulb automatic commit"
        # Create a new commit and update the reference
        commit_hash = commit_to_ref(ref_name, commit_message)
        # Push the reference to the remote repository
        push_ref(ref_name)
            
        # for d in link_dirs:
        #     Path(f"{work_dir}/{d}").symlink_to(f"{project_dir}/{d}")

    


def add_to_queue(action_working_dir, log_dir, action_id, action):
    ip, port = get_manager_address()

    class MyManager(multiprocessing.managers.BaseManager):
        pass

    MyManager.register("add_action")
    manager = MyManager(address=(ip, port), authkey=b"abc")
    manager.connect()

    

    action = {
        'cmd': action,
        'action_id': action_id,
        'working_dir': action_working_dir,
        'log_dir': log_dir,
        'repo_url': run_git_command('git', 'config', '--get', 'remote.origin.url')
    }

    ok = manager.add_action(action)

# Main script execution
def submit(bulb_root, action, name):
    user_config = get_user_config(bulb_root)

    action_id = str(uuid.uuid4())
    action_log_dir = f"{user_config.logs_path}/{action_id}"
    action_working_dir = f"{user_config.runs_path}/{action_id}"

    push_project(action_id, link_dirs=['data'])
    add_to_queue(action_working_dir, action_log_dir, action_id, action)
    log_info(log_dir=action_log_dir, action=action, name=name, action_id=action_id)
