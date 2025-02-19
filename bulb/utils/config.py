import sys
import importlib.util
from pathlib import Path
import bulb.utils.project as project

    
import sys
import importlib.util
from pathlib import Path
from clearconf import BaseConfig

bulb_config = None
default_config = None
global_config = None
project_config = None

def load_config():
    global bulb_config, default_config, global_config, project_config
    # Load all available configs
    default_config = get_default_config()
    default_config = type('DefaultConfig', (default_config, BaseConfig), {})
    bulb_config = default_config
    
    global_config = None
    global_config_path = Path(project.global_bulb_dir) / 'config.py'
    if global_config_path.exists():
        global_config = _load_config_from_path(global_config_path)
        bulb_config = type('BulbConfig', (global_config, bulb_config), {})
        global_config = type('GlobalConfig', (global_config, BaseConfig), {})
    
    project_config = None
    if project.project_bulb_dir is not None:
        project_config_path = Path(project.project_bulb_dir) / 'config.py'
        if project_config_path.exists():
            project_config = _load_config_from_path(project_config_path)
            bulb_config = type('BulbConfig', (project_config, bulb_config), {})
            project_config = type('ProjectConfig', (project_config, BaseConfig), {})

def get_default_config():
    import bulb.configs.config as default_config
    return default_config.Config

def _load_config_from_path(config_path):
    """Load a Config class from a Python file"""
    spec = importlib.util.spec_from_file_location("config", config_path)
    config_module = importlib.util.module_from_spec(spec)
    sys.modules["config"] = config_module
    spec.loader.exec_module(config_module)
    return config_module.Config