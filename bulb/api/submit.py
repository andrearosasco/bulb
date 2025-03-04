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
import bulb.utils.config as config



# Function to save the run script
def push_project(action_id):
        ref_name = f"refs/bulb/{action_id}"
        commit_message = "Bulb automatic commit"

        commit_hash = commit_to_ref(ref_name, commit_message)
        push_ref(ref_name)    


def add_to_queue(action_id, action, tags, resource_group):
    cfg = config.bulb_config

    class MyManager(multiprocessing.managers.BaseManager):
        pass

    MyManager.register("add_action")
    manager = MyManager(address=(cfg.Manager.ip, cfg.Manager.port), authkey=cfg.Manager.authkey)
    manager.connect()

    git_remote = run_git_command('git', 'config', '--get', 'remote.origin.url')

    action = {
        'cmd': action,
        'action_id': action_id,
        'repo_url': git_remote,
        'tags': 'none',
        'resource_group': resource_group,
    }

    ok = manager.add_action(action)

# Main script execution
def submit(action, tags, resource_group):
    action_id = str(uuid.uuid4())

    push_project(action_id)
    add_to_queue(action_id, action, tags, resource_group)
