
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
