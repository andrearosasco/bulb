import json
import multiprocessing
from pathlib import Path
import subprocess
import typer

from bulb.utils.logging import update_json_file
from bulb.utils.config import get_bulb_config

class MyManager(multiprocessing.managers.BaseManager):
    pass

app = typer.Typer()

@app.command()
def start(group: str):
    cfg = get_bulb_config()

    MyManager.register("start_runner")
    manager = MyManager(address=(cfg.Manager.ip, cfg.Manager.port), authkey=cfg.Manager.authkey)
    manager.connect()
    manager.start_runner(group)
    print(f"Runner started")

@app.command()
def list():
    cfg = get_bulb_config()

    MyManager.register("list_runner")
    manager = MyManager(address=(cfg.Manager.ip, cfg.Manager.port), authkey=cfg.Manager.authkey)
    manager.connect()
    runner_list = manager.list_runner()._getvalue()
    print(runner_list)