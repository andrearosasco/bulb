import datetime
import multiprocessing.managers
import subprocess
import os
import json

from bulb.utils.logging import update_json_file

class MyManager(multiprocessing.managers.BaseManager):
    pass

def main():
    job_id = os.environ['PBS_JOBID']

    MyManager.register("get_action")
    manager = MyManager(address=("fe02.priv.franklin.lan", 50000), authkey=b"abc")
    manager.connect()

    for _ in range(2):  
        action_proxy = manager.get_action(job_id=job_id)
        if action_proxy is None or action_proxy._getvalue() is None:
            print("No more actions available")
            break   
        # Convert proxy object to dictionary
        action = {
            'cmd': action_proxy._getvalue()['cmd'],
            'log_dir': action_proxy._getvalue()['log_dir'],
            'working_dir': action_proxy._getvalue()['working_dir']
        }

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
