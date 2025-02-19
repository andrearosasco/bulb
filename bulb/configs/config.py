
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
                'header': ('#PBS -l select=1:ncpus=15:mpiprocs=15:ngpus=1\n'
                           '#PBS -l walltime=03:00:00\n'
                           '#PBS -j oe\n'
                           '#PBS -N bulb\n'
                           '#PBS -q gpu_a100\n')
            },
            'a100f': {
                'header': ('#PBS -l select=1:ncpus=15:mpiprocs=15:ngpus=1\n'
                           '#PBS -l walltime=03:00:00\n'
                           '#PBS -j oe\n'
                           '#PBS -N bulb\n'
                           '#PBS -q a100f\n')
            }
        }
    
