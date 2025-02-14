import datetime
import multiprocessing.managers
import subprocess
import os
import json

from bulb.utils.git import checkout_ref, clone_repo, fetch_ref
from bulb.utils.logging import update_json_file
from bulb.utils.misc import get_default_config


def download_code(repo_url, ref_name, work_dir):
    clone_repo(repo_url, work_dir)
    fetch_ref(work_dir, ref_name)
    checkout_ref(work_dir, ref_name)


class MyManager(multiprocessing.managers.BaseManager):
    pass

def main():
    cfg = get_default_config()

    job_id = os.environ.get('PBS_JOBID', None)

    MyManager.register("get_action")
    manager = MyManager(address=("fe02.priv.franklin.lan", 60000), authkey=b"abc")
    manager.connect()

    for _ in range(1):  
        action_proxy = manager.get_action(job_id=job_id)
        if action_proxy is None or action_proxy._getvalue() is None:
            print("No more actions available")
            break   
        # Convert proxy object to dictionary
        action = action_proxy._getvalue()

        log_dir = cfg.logs_path / action['action_id']
        work_dir = cfg.runs_path / action['action_id']
        ref_name = f'refs/bulb/{action["action_id"]}'

        download_code(action['repo_url'], ref_name, work_dir)

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
        update_json_file(f'{log_dir}/meta.json', meta_updates)

        with open(f'{log_dir}/output.log', 'w+', buffering=1) as f:
            result = subprocess.run(
                action['cmd'].split(), 
                stdout=f,
                stderr=f,
                text=True, 
                cwd=work_dir,
                env=env_vars
            )
        
        # Update meta info with completion status and end time
        meta_updates = {
            'status': 'Success' if result.returncode == 0 else f'Failed ({result.returncode})',
            'end_time': datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        }
        update_json_file(f'{log_dir}/meta.json', meta_updates)
        print(result.stdout)

if __name__ == "__main__":
    main()
