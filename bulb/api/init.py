from pathlib import Path
from pathlib import Path
import os
import bulb


def get_configs_path():
    configs_path = Path(os.path.abspath(bulb.__file__)).parent / "configs"
    return configs_path


def init(project_root: Path, exists_ok: bool = False):
    # find project root 
    bulb_dir = project_root / ".bulb"

    if bulb_dir.exists() and not bulb_dir.is_dir():
        raise FileExistsError(f"{bulb_dir} already exists and is not a directory.")
    
    if bulb_dir.is_dir() and not exists_ok:
        raise FileExistsError(f"Project already initialized at {project_root}.")
    
    bulb_dir.mkdir()
    (bulb_dir / 'configs').symlink_to(get_configs_path())