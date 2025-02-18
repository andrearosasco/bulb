from pathlib import Path
from typing import Literal

bulb_project_root = None

def find_git_root() -> Path:
    return find_root("git")

def find_bulb_project_root() -> Path:
    global bulb_project_root
    bulb_project_root = find_root("bulb")
    return bulb_project_root

def find_root(type:Literal["git", "bulb"]) -> Path:
    """
    Find the project root directory by looking for a .git directory.
    """
    current_dir = Path.cwd()

    i = 0
    while current_dir != Path("/"):
        if (current_dir / f".{type}").is_dir():
            return current_dir
        
        if current_dir == Path("/") or i > 10:
            raise FileNotFoundError("Could not find project root.")

        current_dir = current_dir.parent
        i += 1