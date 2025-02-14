#!/bin/bash

tmux="/work/arosasco/miniforge3/bin/tmux"

JOB_SCRIPT=$(cat <<EOF
#!/bin/bash
#PBS -l select=1:ncpus=15:mpiprocs=15:ngpus=1
#PBS -l walltime=3:00:00
#PBS -j oe
#PBS -N interactive
#PBS -q a100f

SESSION=\$(echo "job_\$PBS_JOBID" | cut -d'.' -f1)

$tmux -L \$SESSION  new-session -d -s \$SESSION
$tmux -L \$SESSION  send-keys -t \$SESSION "python /home/arosasco/scripts/runner.py; qdel \$PBS_JOBID" C-m

tail -f /dev/null
EOF
)

# Submit the job
echo "$JOB_SCRIPT" | qsub
