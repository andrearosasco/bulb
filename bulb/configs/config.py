
from pathlib import Path

class Config:
    class Manager:
        ip = 'localhost'
        port = 50000
        authkey = b"abc"
        log_path = Path.home() / ".bulb"

    class Runner:
        runs_path = Path.home() / '.bulb/runs'
        logs_path = Path.home() / '.bulb/logs'

        links = {}
        cmd_format = {}

        groups = {
            'gpu_a100': {
                'header': """
                    PBS -l select=1:ncpus=15:mpiprocs=15:ngpus=1
                    PBS -l walltime=03:00:00
                    PBS -j oe
                    PBS -N bulb
                    PBS -q gpu_a100
                """,
            },
            'a100f': {
                'header': """
                    PBS -l select=1:ncpus=15:mpiprocs=15:ngpus=1
                    PBS -l walltime=03:00:00
                    PBS -j oe
                    PBS -N bulb
                    PBS -q a100f
                """
            }
        }
    
