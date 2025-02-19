from pathlib import Path
import os
import bulb
from shutil import copy


configs_path = Path(os.path.abspath(bulb.__file__)).parent / "configs/config.py"


def init(project_root: Path):
    # find project root 
    bulb_dir = project_root / ".bulb"

    if bulb_dir.exists() and not bulb_dir.is_dir():
        raise FileExistsError(f"{bulb_dir} already exists and is not a directory.")

    if not bulb_dir.exists():
        bulb_dir.mkdir()

    if not (bulb_dir / 'config.py').exists():
        copy(configs_path, bulb_dir / 'config.py')
