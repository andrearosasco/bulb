import json
import multiprocessing
from pathlib import Path
import subprocess
import typer

from bulb.utils.logging import update_json_file
from bulb.utils.misc import get_manager_address
from bulb.configs.config import Config as cfg

class MyManager(multiprocessing.managers.BaseManager):
    pass

manager_log_path = cfg.manager_log_path
manager_log_path.mkdir(exist_ok=True)

app = typer.Typer()

@app.command()
def start(port:int = 50000):
    
    with open(f'{manager_log_path}/manager.log', 'a+', buffering=1) as f:
        subprocess.Popen(['nohup', 'bulb-manager', '--port', str(port)], 
                         stdout=f, stderr=f)

@app.command()
def stop():
    ip, port = get_manager_address()

    MyManager.register("stop")
    manager = MyManager(address=(ip, port), authkey=b"abc")
    manager.connect()
    manager.stop()

@app.command()
def config(ip:str = "localhost", port:int = 50000):
    update_json_file(f'{manager_log_path}/manager.json', {'ip': ip, 'port': port})

from rich.console import Console
from rich.table import Table
@app.command()
def status():
    ip, port = get_manager_address()

    MyManager.register("status")
    manager = MyManager(address=(ip, port), authkey=b"abc")
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
    ip, port = get_manager_address()

    MyManager.register("lock")
    manager = MyManager(address=(ip, port), authkey=b"abc")
    manager.connect()
    manager.lock()

@app.command()
def unlock():
    ip, port = get_manager_address()

    MyManager.register("unlock")
    manager = MyManager(address=(ip, port), authkey=b"abc")
    manager.connect()
    manager.unlock()

@app.command()
def submit(action:str):
    class MyManager(multiprocessing.managers.BaseManager):
        pass

    MyManager.register("add_action")
    manager = MyManager(address=("localhost", 50000), authkey=b"abc")
    manager.connect()

    action = {
        'cmd': action,
        'working_dir': Path.cwd().as_posix(),
        'log_dir': Path.cwd().as_posix()
    }

    ok = manager.add_action(action)

@app.command()
def pop(idx:int = 0):
    ip, port = get_manager_address()

    MyManager.register("get_action")
    manager = MyManager(address=(ip, port), authkey=b"abc")
    manager.connect()

    action_proxy = manager.get_action(index=idx)
    if action_proxy is None or action_proxy._getvalue() is None:
        print("No actions available")   
    else:
        # Convert proxy object to dictionary
        action = {
            'cmd': action_proxy._getvalue()['cmd'],
            'log_dir': action_proxy._getvalue()['log_dir'],
            'working_dir': action_proxy._getvalue()['working_dir']
        }
        print(action)


