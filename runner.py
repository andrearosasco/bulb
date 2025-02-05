import multiprocessing.managers
import subprocess
import os

class MyManager(multiprocessing.managers.BaseManager):
    pass

def main():
    job_id = os.environ['PBS_JOBID']

    MyManager.register("get_action")
    manager = MyManager(address=("fe01.priv.franklin.lan", 50000), authkey=b"abc")
    manager.connect()

    for _ in range(3):  
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

        print(f"Executing: {action['cmd']}")

        with open(f'{action["log_dir"]}/status.txt', 'w+') as f:
            f.write('Running')

        with open(f'{action["log_dir"]}/output.log', 'w+') as f:
            result = subprocess.run(action['cmd'], shell=True, stdout=f, stderr=f, text=True, cwd=action['working_dir'])
        
        with open(f'{action["log_dir"]}/status.txt', 'w+') as f:
            if result.returncode == 0:
                f.write('Success')
            else:
                f.write('Failed with return code: ' + str(result.returncode))

        print(result.stdout)

if __name__ == "__main__":
    main()
