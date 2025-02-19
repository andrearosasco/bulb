import json
import multiprocessing
from pathlib import Path
import subprocess
import typer

from bulb.utils.logging import update_json_file
import bulb.utils.config as config

class MyManager(multiprocessing.managers.BaseManager):
    pass



app = typer.Typer()

@app.command()
def start(port:int = 50000):
    cfg = config.bulb_config
    manager_log_path = cfg.Manager.log_path
    manager_log_path.mkdir(exist_ok=True)
    
    with open(f'{manager_log_path}/manager.log', 'a+', buffering=1) as f:
        subprocess.Popen(['nohup', 'bulb-manager', '--port', str(port)], 
                         stdout=f, stderr=f)

@app.command()
def stop(ip:str = None, port:int = None, authkey:str = None):
    cfg = config.bulb_config
    if ip is None:
        ip = cfg.Manager.ip
    
    if port is None:
        port = cfg.Manager.port

    if authkey is None:
        authkey = cfg.Manager.authkey


    MyManager.register("stop")
    manager = MyManager(address=(cfg.Manager.ip, cfg.Manager.port), authkey=cfg.Manager.authkey)
    manager.connect()
    manager.stop()


from rich.console import Console
from rich.table import Table
@app.command()
def status():
    cfg = config.bulb_config

    MyManager.register("status")
    manager = MyManager(address=(cfg.Manager.ip, cfg.Manager.port), authkey=cfg.Manager.authkey)
    manager.connect()
    status_list = manager.status()._getvalue()

    # Create table
    table = Table(show_header=True, header_style="bold magenta")
    
    # Add index column
    table.add_column("#", style="cyan", no_wrap=True)
    
    # Dynamically add columns based on the first dictionary's keys
    if status_list and len(status_list) > 0:
        for key in status_list[0].keys():
            table.add_column(key.capitalize(), style="green")
    
    # Add rows with index
    for idx, status_dict in enumerate(status_list):
        row = [str(idx)]  # Start with index
        row.extend(str(value) for value in status_dict.values())
        table.add_row(*row)
    
    # Create console and print table
    console = Console()
    console.print(table)

@app.command()
def lock():
    cfg = config.bulb_config

    MyManager.register("lock")
    manager = MyManager(address=(cfg.Manager.ip, cfg.Manager.port), authkey=cfg.Manager.authkey)
    manager.connect()
    manager.lock()

@app.command()
def unlock():
    cfg = config.bulb_config

    MyManager.register("unlock")
    manager = MyManager(address=(cfg.Manager.ip, cfg.Manager.port), authkey=cfg.Manager.authkey)
    manager.connect()
    manager.unlock()

@app.command()
def submit(action:str):
    cfg = config.bulb_config

    class MyManager(multiprocessing.managers.BaseManager):
        pass

    MyManager.register("add_action")
    manager = MyManager(address=(cfg.Manager.ip, cfg.Manager.port), authkey=cfg.Manager.authkey)
    manager.connect()

    action = {
        'cmd': action,
        'working_dir': Path.cwd().as_posix(),
        'log_dir': Path.cwd().as_posix()
    }

    ok = manager.add_action(action)

@app.command()
def pop(idx:int = 0):
    cfg = config.bulb_config

    MyManager.register("get_action")
    manager = MyManager(address=(cfg.Manager.ip, cfg.Manager.port), authkey=cfg.Manager.authkey)
    manager.connect()

    action_proxy = manager.get_action(index=idx)
    if action_proxy is None or action_proxy._getvalue() is None:
        print("No actions available")
        return
    action = action_proxy._getvalue()
    print(action)


