
from pathlib import Path

class Config:
    manager_log_path = Path.home() / ".bulb"
    runs_path = Path.home() / '.bulb/runs'
    logs_path = Path.home() / '.bulb/logs'
    