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
def start(group: str, num_runner: int = 1, ip: str = None, port: int = None, authkey: str = None):
    cfg = config.bulb_config

    cfg = config.bulb_config
    if ip is None:
        ip = cfg.Manager.ip
    
    if port is None:
        port = cfg.Manager.port

    if authkey is None:
        authkey = cfg.Manager.authkey

    MyManager.register("start_runner")
    manager = MyManager(address=(cfg.Manager.ip, cfg.Manager.port), authkey=cfg.Manager.authkey)
    manager.connect()
    for _ in range(num_runner):
        manager.start_runner(group)

@app.command()
def list():
    cfg = config.bulb_config

    MyManager.register("list_runner")
    manager = MyManager(address=(cfg.Manager.ip, cfg.Manager.port), authkey=cfg.Manager.authkey)
    manager.connect()
    runner_list = manager.list_runner()._getvalue()
    print(runner_list)