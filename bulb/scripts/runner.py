import datetime
import multiprocessing.managers
import subprocess
import os
import json

from bulb.utils.git import checkout_ref, clone_repo, fetch_ref
from bulb.utils.logging import update_json_file


def download_code(repo_url, action_id):
    ref_name = f"refs/bulb/{action_id}"
    clone_dir = f"/tmp/{action_id}"
    clone_repo(repo_url, clone_dir)
    fetch_ref(clone_dir, ref_name)
    checkout_ref(clone_dir, ref_name)


class MyManager(multiprocessing.managers.BaseManager):
    pass

def main():
    job_id = os.environ.get('PBS_JOBID', None)

    MyManager.register("get_action")
    manager = MyManager(address=("fe02.priv.franklin.lan", 50000), authkey=b"abc")
    manager.connect()

    for _ in range(1):  
        action_proxy = manager.get_action(job_id=job_id)
        if action_proxy is None or action_proxy._getvalue() is None:
            print("No more actions available")
            break   
        # Convert proxy object to dictionary
        action = action_proxy._getvalue()

        download_code(action['repo_url'], action['action_id'])

        # Create environment variables
        env_vars = {f"BULB_{k.upper()}": str(v) for k, v in action.items()}
        env_vars.update(os.environ.copy())  # Keep existing env vars

        print(f"Executing: {action['cmd']}")

        # Write meta info to JSON
        meta_updates = {
            'job_id': job_id,
            'hostname': os.environ.get("HOSTNAME", ""),
            'status': 'Running',
            'start_time': datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        }
        update_json_file(f'{action["log_dir"]}/meta.json', meta_updates)

        with open(f'{action["log_dir"]}/output.log', 'w+', buffering=1) as f:
            result = subprocess.run(
                action['cmd'].split(), 
                stdout=f,
                stderr=f,
                text=True, 
                cwd=action['working_dir'],
                env=env_vars
            )
        
        # Update meta info with completion status and end time
        meta_updates = {
            'status': 'Success' if result.returncode == 0 else f'Failed ({result.returncode})',
            'end_time': datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        }
        update_json_file(f'{action["log_dir"]}/meta.json', meta_updates)
        print(result.stdout)

if __name__ == "__main__":
    main()
