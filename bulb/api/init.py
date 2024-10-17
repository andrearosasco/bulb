from pathlib import Path
from pathlib import Path
import os
import bulb


def get_configs_path():
    configs_path = Path(os.path.abspath(bulb.__file__)).parent / "configs"
    return configs_path


def init(project_root: Path):
    # find project root 
    bulb_dir = project_root / ".bulb"

    if bulb_dir.is_dir():
        raise FileExistsError(f"Project already initialized at {project_root}.")
    if bulb_dir.exists():
        raise FileExistsError(f"{bulb_dir} already exists and is not a directory.")
    
    bulb_dir.mkdir()
    (bulb_dir / 'configs').symlink_to(get_configs_path())