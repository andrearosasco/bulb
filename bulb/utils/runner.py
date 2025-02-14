import os
import stat
import tempfile

from bulb.utils.misc import get_global_config

def generate_pbs_script(
    queue_name='gpu_a100',
    time='03:00:00',
    select=1,
    ncpus=15,
    mpiprocs=15,
    ngpus=1,
    job_name="interactive",
    tmux_path="/work/arosasco/miniforge3/bin/tmux",
    worker_script="bulb.scripts.runner"
):
    cfg = get_global_config()
    # Create the content of the job script (PBS part)
    job_script_content = f'''#!/bin/bash
#PBS -l select={select}:ncpus={ncpus}:mpiprocs={mpiprocs}:ngpus={ngpus}
#PBS -l walltime={time}
#PBS -j oe
#PBS -N {job_name}
#PBS -q {queue_name}

SESSION=\\$(echo "job_\\$PBS_JOBID" | cut -d'.' -f1)

$tmux -L \\$SESSION  new-session -d -s \\$SESSION
$tmux -L \\$SESSION  send-keys -t \\$SESSION "{cfg.python} -m {worker_script}; qdel \\$PBS_JOBID" C-m

tail -f /dev/null
'''

    # Create the wrapper script content
    wrapper_script_content = f'''#!/bin/bash

tmux="{tmux_path}"

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