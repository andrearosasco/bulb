import os
import subprocess
import tempfile
import datetime
from pathlib import Path
import atexit
import uuid
import multiprocessing.managers
import json

from bulb.configs.config import ProjectConfig, ExperimentConfig
    

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

    with open(f"{log_dir}/file.patch", 'w') as f:
        f.write(git_diff)

# Function to save the run script
def clone_project(project_dir, work_dir, patch_file, link_dirs):

    # Set up work directory
    # Path(work_dir).parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(f'git clone {project_dir} {work_dir}'.split())
    subprocess.run(f'git apply --whitespace=nowarn --allow-empty {patch_file}'.split(), cwd=work_dir)
    
    for d in link_dirs:
        Path(f"{work_dir}/{d}").symlink_to(f"{project_dir}/{d}")

    # git config advice.detachedHead false
    # git checkout --force --quiet "{EXP_HASH}"


def add_to_queue(action_working_dir, log_dir, action):
    class MyManager(multiprocessing.managers.BaseManager):
        pass

    MyManager.register("add_action")
    manager = MyManager(address=("localhost", 50000), authkey=b"abc")
    manager.connect()

    action = {
        'cmd': action,
        'working_dir': action_working_dir,
        'log_dir': log_dir
    }

    ok = manager.add_action(action)

# Main script execution
def submit(bulb_root, action, name):
    action_id = str(uuid.uuid4())
    action_log_dir = f"/fastwork/arosasco/bulb/logs/{action_id}"
    action_working_dir = f"/fastwork/arosasco/bulb/runs/{action_id}"

    log_info(log_dir=action_log_dir, action=action, name=name, action_id=action_id)
    clone_project(bulb_root, action_working_dir, patch_file=f'{action_log_dir}/file.patch', link_dirs=['data'])
    add_to_queue(action_working_dir, action_log_dir, action)
