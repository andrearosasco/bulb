import os
from pathlib import Path
from shutil import copy
from typing import Literal

import bulb

project_bulb_dir = None
global_bulb_dir = None
git_dir = None
project_root = None

_configs_path = Path(os.path.abspath(bulb.__file__)).parent / "configs/config_commented.py"

def load_paths(create=False):
    global git_dir, project_root, project_bulb_dir, global_bulb_dir

    global_bulb_dir = check_bulb_dir(Path.home() / '.bulb', True)

    git_dir = find_root("git")

    if git_dir is not None:
        project_root = git_dir.parent
        project_bulb_dir = check_bulb_dir(project_root / '.bulb', create)
    

def check_bulb_dir(bulb_dir:Path, create):
    if bulb_dir.exists() and not bulb_dir.is_dir():
        raise FileExistsError(f"{bulb_dir} already exists and is not a directory.")

    if not create:
        return bulb_dir if (bulb_dir / 'config.py').exists() else None

    if not bulb_dir.exists():
        bulb_dir.mkdir()

    if not (bulb_dir / 'config.py').exists():
        copy(_configs_path, bulb_dir / 'config.py')

    return bulb_dir


def find_root(type:Literal["git", "bulb"]) -> Path:
    """
    Find the project root directory by looking for a .git directory.
    """
    current_dir = Path.cwd()

    i = 0
    while current_dir != Path("/"):
        if (current_dir / f".{type}").is_dir():
            return current_dir / f".{type}"
        
        if current_dir == Path("/") or i > 10:
            return

        current_dir = current_dir.parent
        i += 1