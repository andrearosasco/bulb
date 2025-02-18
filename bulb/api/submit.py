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
from bulb.utils.config import get_bulb_config



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

    


def add_to_queue(action_id, action):
    cfg = get_bulb_config()

    class MyManager(multiprocessing.managers.BaseManager):
        pass

    MyManager.register("add_action")
    manager = MyManager(address=(cfg.Manager.ip, cfg.Manager.port), authkey=cfg.Manager.authkey)
    manager.connect()

    action = {
        'cmd': action,
        'action_id': action_id,
        'repo_url': run_git_command('git', 'config', '--get', 'remote.origin.url'),
        'tags': [],
        'resource_group': 'any',
    }

    ok = manager.add_action(action)

# Main script execution
def submit(bulb_root, action, name):
    cfg = get_bulb_config()

    action_id = str(uuid.uuid4())

    push_project(action_id, link_dirs=['data'])
    add_to_queue(action_id, action)
