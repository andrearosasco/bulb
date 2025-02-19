import json
import logging
import shutil
from pathlib import Path
import os
import rich

import bulb
import bulb.utils.config as cfg
import bulb.utils.project as project

from bulb import api
import typer
from typing_extensions import Annotated

from clearconf import BaseConfig

from bulb.cli import manager
from bulb.cli import runner
from bulb.utils.logging import logger
# import debugpy
# debugpy.listen(5678)
# print('Waiting for debugger to attach...')
# debugpy.wait_for_client()

app = typer.Typer()
app.add_typer(manager.app, name="manager")
app.add_typer(runner.app, name="runner")

@app.command()
def status():
    pass

@app.command()
def config(
    project: Annotated[bool, typer.Option("--project", help="Display project config")] = False,
    default: Annotated[bool, typer.Option("--default", help="Display default config")] = False,
    global_: Annotated[bool, typer.Option("--global", help="Display global config")] = False,
):
    options = sum([project, default, global_])
    if options > 1:
        logger.error("Please specify only one config option")
        raise typer.Exit(1)
        
    if project:
        if cfg.project_config:
            rich.print(json.dumps(cfg.project_config.to_dict(), indent=4))
        else:
            logger.warning("No project config found")
    elif default:
        rich.print(json.dumps(cfg.default_config.to_dict(), indent=4))
    elif global_:
        rich.print(json.dumps(cfg.global_config.to_dict(), indent=4))
    else:
        rich.print(json.dumps(cfg.bulb_config.to_dict(), indent=4))

@app.command()
def submit(action:str, tags:str='', resource_group:str='any'):
    if project.project_root is None:
        logger.error("Jobs can only be submitted from inside a git repo.")
        return
    api.submit(action, tags, resource_group)


@app.callback()
def setup(verbose: bool = False):
    """
    bulb CLI can be used to prepare
    and run your experiments.
    """
    project.load_paths()
    cfg.load_config()

def main():
    app()
