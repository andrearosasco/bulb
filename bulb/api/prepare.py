import os
import subprocess
import tempfile
import datetime
from pathlib import Path
import atexit

from bulb.configs.config import ProjectConfig, ExperimentConfig
    

# Function to clean up temporary files
def cleanup():
    if os.path.exists(temp_file.name):
        os.remove(temp_file.name)

# Function to get user input
def get_user_input():
    EXPERIMENT_DESCRIPTION = ""
    
    with open(temp_file.name, 'w') as f:
        f.write(f"{experiment_name}\n{EXPERIMENT_DESCRIPTION}\n")
    
    editor = os.getenv('EDITOR', 'vim')
    subprocess.call([editor, temp_file.name])
    
    with open(temp_file.name, 'r') as f:
        lines = f.readlines()
        experiment_name = lines[0].strip()
        EXPERIMENT_DESCRIPTION = " ".join(line.strip() for line in lines[1:]).strip()

# Function to validate experiment description
def validate_experiment_description():
    if not EXPERIMENT_DESCRIPTION:
        print("Experiment description is empty. Exiting.")
        exit(1)

# Function to set up directories and save git info
def setup_directories_and_git_info():
    global LOG_DIR, WORK_DIR, EXP_HASH

    os.chdir(project_dir)
    LOG_DIR = f"{project_dir}/data/diffusion_transformer_transport_ph/evaluations/checkpoint3/{experiment_name}"
    WORK_DIR = f"/fastwork/arosasco/{experiment_name}"
    EXP_HASH = subprocess.check_output(['git', 'rev-parse', 'HEAD']).strip().decode()

    os.makedirs(f"{LOG_DIR}/.bulb", exist_ok=True)
    with open(f"{LOG_DIR}/.bulb/description.txt", 'w') as f:
        f.write(EXPERIMENT_DESCRIPTION)
    with open(f"{LOG_DIR}/.bulb/commit.txt", 'w') as f:
        f.write(EXP_HASH)
    with open(f"{LOG_DIR}/.bulb/status.txt", 'w') as f:
        f.write("Not started")

    git_diff = subprocess.check_output(['git', 'diff', 'HEAD']).decode()
    with open(f"{LOG_DIR}/.bulb/file.patch", 'w') as f:
        f.write(git_diff)
    
    subprocess.call(['logger', '-s', '-p', 'local0.info', f"Commit hash and patch saved in {LOG_DIR}"])
    subprocess.call(['logger', '-s', '-p', 'local0.info', f"Commit hash: {EXP_HASH}"])

# Function to save the run script
def save_run_script():
    with open(f"{LOG_DIR}/out.txt", 'w') as f:
        f.write("Your experiment output will appear here")
    
    RUN_SCRIPT = f"{LOG_DIR}/.bulb/run_script.sh"
    
    run_script_content = f"""#!/bin/bash

set -e  # Exit immediately if a command exits with a non-zero status.
set -o pipefail  # Return value of a pipeline is the value of the last command to exit with a non-zero status, or zero if all commands exit successfully.
set -u  # Treat unset variables as an error when substituting.

LOG_DIR="$(dirname "$0")/.."

# Set up work directory
rm -rf {WORK_DIR} && mkdir -p "{WORK_DIR}" && cd "{WORK_DIR}"
ln -s "{project_dir}/data" ./data
cp -r "{project_dir}/.git" ./

git config advice.detachedHead false
git checkout --force --quiet "{EXP_HASH}"
git apply --whitespace=nowarn --allow-empty "$LOG_DIR/.bulb/file.patch"

PORT=$(shuf -n 1 -i 49152-65535)

while true; do
  if nc -z localhost $PORT; then
    echo "Port $PORT is in use"
    PORT=$(shuf -n 1 -i 49152-65535)
  else
    echo "Found free port: $PORT"
    break
  fi
done

echo "Scheduled as $PBS_JOBID" > $LOG_DIR/.bulb/info.txt
echo "Running $(hostname)$(pwd)" >> $LOG_DIR/.bulb/info.txt
echo "Debugger listening at port: $PORT" >> $LOG_DIR/.bulb/info.txt

echo "Running..." > $LOG_DIR/.bulb/status.txt

singularity exec --nv -B /usr/share/glvnd  \\
    --writable-tmpfs {project_dir}/robodiff_latest.sif \\
    python -m debugpy --listen $PORT {WORK_DIR}/eval.py \\
        --checkpoint {project_dir}/data/diffusion_transformer_transport_ph/checkpoints/3_epoch=3350-test_mean_score=0.955.ckpt \\
        --output_dir $LOG_DIR \\
        --device cuda:0 >> $LOG_DIR/out.txt 2>&1

echo "Finished with exit code $?" > $LOG_DIR/.bulb/status.txt
"""

    with open(RUN_SCRIPT, 'w') as f:
        f.write(run_script_content)
    
    os.chmod(RUN_SCRIPT, 0o755)
    subprocess.call(['logger', '-s', '-p', 'local0.info', f"Run script saved at {RUN_SCRIPT}"])

# Function to update the project database
def update_project_database():
    BULB_DIR = f"{project_dir}/.bulb"
    DATABASE_FILE = f"{BULB_DIR}/database.txt"
    
    os.makedirs(BULB_DIR, exist_ok=True)
    
    database_content = f"{experiment_name} : {LOG_DIR}\n"
    if os.path.exists(DATABASE_FILE):
        with open(DATABASE_FILE, 'r') as f:
            database_content += f.read()

    with open(DATABASE_FILE, 'w') as f:
        f.write(database_content)

    subprocess.call(['logger', '-s', '-p', 'local0.info', f"Experiment added to project database: {experiment_name} -> {LOG_DIR}"])

# Main script execution
def prepare(bulb_root):

    runner = ExperimentConfig.runner
    project_dir = ProjectConfig.project_dir
    experiment_name = ExperimentConfig.experiment_name

    temp_file = tempfile.NamedTemporaryFile(delete=False)
    atexit.register(cleanup)

    
    editor = os.getenv('EDITOR', 'vim')
    subprocess.call([editor, temp_file.name])
    
    with open(temp_file.name, 'r') as f:
        lines = f.readlines()
        experiment_name = lines[0].strip()
        EXPERIMENT_DESCRIPTION = " ".join(line.strip() for line in lines[1:]).strip()

    get_user_input()
    validate_experiment_description()
    setup_directories_and_git_info()
    save_run_script()
    update_project_database()
