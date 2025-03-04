import os
import stat
import subprocess
import sys
import tempfile

def pbs_del(job_id):
    """Delete a PBS job by ID."""
    subprocess.run(["qdel", job_id], check=True, text=True, capture_output=True)

def generate_pbs_script(
    pbs_header,
    resource_group,
    tmux_path="/work/arosasco/miniforge3/bin/tmux"
):
    worker_script="bulb.scripts.runner"
    # Create the content of the job script (PBS part)
    job_script_content = f'''#!/bin/bash
{pbs_header}

# Declare environment variable
export BULB_RESOURCE_GROUP={resource_group}
{sys.executable} -m {worker_script};
'''

    # Create the wrapper script content
    wrapper_script_content = f'''#!/bin/bash

JOB_SCRIPT=$(cat <<EOF
{job_script_content}
EOF
)

# Submit the job
echo "$JOB_SCRIPT" | qsub
'''

    # Create a temporary file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.sh') as tmp_file:
        tmp_file.write(wrapper_script_content)
        tmp_path = tmp_file.name

    os.chmod(tmp_path, stat.S_IRWXU)  # Read, write, and execute permissions for the owner

    return tmp_path
