import logging
import shutil
from pathlib import Path
import os

import bulb
from bulb.utils.git import find_git_root, find_bulb_root
from bulb import api
import typer
from typing_extensions import Annotated

from bulb.cli import defaults

app = typer.Typer()
# app.add_typer(defaults.app, name="defaults")

@app.command()
def init(

    verbose:bool=False
    ):
    """
    Initialize Bulb

    Creates a .bulb directory in your project root.
    If not specifided, the project root is determined by searching for a .git directory in the current or parent directories.
    If a .git directory is not found Bulb is initialized in the current directory.
    """
    # find project root 
    try:
        project_root = find_git_root()
    except FileNotFoundError as e:
        logging.success('Could not determine project root')
        project_root = Path.cwd()

    try:
        api.init(project_root)
        logging.success(f"Initialized bulb project at {project_root}.")
    except FileExistsError as e:
        print(e)


@app.command()
def prepare():
    # find project root 

    try: bulb_root = find_bulb_root()
    except FileNotFoundError as e: 

        try:
            git_root = find_git_root()
        except FileNotFoundError as e:
            print('Could not find project root. Please check https://bulb/initialization for more information.')
            return

    try:
        api.init(git_root)
        bulb_root = git_root
    except FileExistsError as e:
        print(e)
        
    api.prepare(bulb_root)



@app.callback()
def doc():
    """
    bulb CLI can be used to prepare
    and run your experiments.
    """


def main():
    app()