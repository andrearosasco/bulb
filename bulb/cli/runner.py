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
def start():
    ip, port = get_manager_address()

    MyManager.register("start_runner")
    manager = MyManager(address=(ip, port), authkey=b"abc")
    manager.connect()
    manager.start_runner()
    print(f"Runner started")

@app.command()
def list():
    ip, port = get_manager_address()

    MyManager.register("list_runner")
    manager = MyManager(address=(ip, port), authkey=b"abc")
    manager.connect()
    runner_list = manager.list_runner()._getvalue()
    print(runner_list)