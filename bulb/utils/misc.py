import importlib
import json
from pathlib import Path
import sys
from bulb.configs.config import Config as cfg

def get_manager_address():
    try:
        with open(f'{cfg.manager_log_path}/manager.json') as f:
            config = json.load(f)
            ip = config.get('ip', 'localhost')
            port = config.get('port', 50000)
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        ip = 'localhost'
        port = 50000
    return ip, port

def get_user_config(bulb_root):
    config_path = f'{bulb_root}/.bulb/config.py'
    spec = importlib.util.spec_from_file_location("config", config_path)
    config_module = importlib.util.module_from_spec(spec)
    sys.modules["config"] = config_module
    spec.loader.exec_module(config_module)
    
    # Get the Config class from the module
    Config = config_module.Config
    return Config

def get_global_config():
    config_path = Path.home() / '.bulb/config.py'
    spec = importlib.util.spec_from_file_location("config", config_path)
    config_module = importlib.util.module_from_spec(spec)
    sys.modules["config"] = config_module
    spec.loader.exec_module(config_module)
    
    # Get the Config class from the module
    Config = config_module.Config
    return Config

def get_default_config():
    import bulb.configs.config as config
    return config.Config