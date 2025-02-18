import sys
import importlib.util
from pathlib import Path
import bulb.utils.project as project

    
import sys
import importlib.util
from pathlib import Path

def get_bulb_config():
    # Load all available configs
    default_config = get_default_config()
    
    global_config = None
    global_config_path = Path.home() / '.bulb/config.py'
    if global_config_path.exists():
        global_config = _load_config_from_path(global_config_path)
    
    user_config = None
    if project.bulb_project_root is not None:
        user_config_path = Path(project.bulb_project_root) / '.bulb/config.py'
        if user_config_path.exists():
            user_config = _load_config_from_path(user_config_path)
    
    # Collect configs in precedence order: user > global > default
    configs = [c for c in [user_config, global_config, default_config] if c is not None]
    
    # Recursively merge configurations
    MergedConfig = _merge_config_classes(*configs)
    return MergedConfig

def _merge_config_classes(*config_classes):
    """Recursively merge configuration classes with nested class support"""
    merged_attrs = {}

    # Collect all unique attribute names from all config classes
    all_attr_names = set()
    for config_cls in config_classes:
        all_attr_names.update(dir(config_cls))
    all_attr_names = [n for n in all_attr_names if not n.startswith('__')]

    for attr_name in all_attr_names:
        # Collect values from all configs in precedence order
        values = []
        for config_cls in config_classes:
            if hasattr(config_cls, attr_name):
                values.append(getattr(config_cls, attr_name))

        # Handle nested classes recursively
        if all(isinstance(v, type) for v in values):
            merged_attrs[attr_name] = _merge_config_classes(*values)
        else:
            # Take the first non-class value (highest precedence)
            for v in values:
                if not isinstance(v, type):
                    merged_attrs[attr_name] = v
                    break
            else:
                # If all are classes but we're in else clause, take first
                merged_attrs[attr_name] = values[0]

    return type('MergedConfig', (), merged_attrs)

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