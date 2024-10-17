import os
import sys
import subprocess

def main(args):
    if len(args) < 2:
        print("Usage: python script.py <index1,index2:...>")
        sys.exit(1)

    # Join all arguments into a single string and remove any spaces
    input_indices = ''.join(args[1:]).replace(' ', '')
    
    # Split the indices by ':'
    sequence_groups = input_indices.split(':')

    # Define the paths
    database_file = '.bulb/database.txt'
    pbs_output_file = '.bulb/pbs_script.pbs'

    # Read the database file and parse the experiment names and paths
    experiments = {}
    with open(database_file, 'r') as db_file:
        for line in db_file:
            if line.strip():  # Skip empty lines
                experiment_name, experiment_path = line.strip().split(' : ')
                experiments[experiment_name] = experiment_path

    # Prepare the list of selected experiments
    selected_experiments = []
    for group in sequence_groups:
        # Sequential execution within each group (separated by ',')
        sequential_experiments = [list(experiments.items())[int(index) - 1] for index in group.split(',')]
        selected_experiments.append(sequential_experiments)

    # Generate PBS script content
    pbs_script_content = 'tmux=/work/arosasco/miniforge3/bin/tmux\n'
    pbs_script_content += 'session=$(echo "job_$PBS_JOBID" | cut -d\'.\' -f1)\n\n'
    pbs_script_content += f"$tmux new-session -d -s ${{session}}\n\n"
    for i, sequential_group in enumerate(selected_experiments):
        # Create a subshell for each group to allow parallel execution between groups
        
        for j, (exp_name, exp_path) in enumerate(sequential_group):
            run_script_path = os.path.join(exp_path, '.bulb', 'run_script.sh')
            if os.path.exists(run_script_path):
                pbs_script_content += f'$tmux send-keys -t ${{session}} "$tmux wait ping_${{session}}__{i}_{j}; bash {run_script_path}; $tmux wait -S ping_${{session}}__{i}_{j+1}" Enter\n'
                if j != len(sequential_group) - 1:
                    pbs_script_content += f'$tmux split-window -v -t ${{session}}\n'
            else:
                pbs_script_content += f"echo 'Warning: {run_script_path} not found for {exp_name}'\n"
 
        pbs_script_content += f'$tmux select-layout -t ${{session}} tiled\n\n'
        if i != len(selected_experiments) - 1:
            pbs_script_content += f'$tmux new-window -t ${{session}}\n'

    for i in range(len(selected_experiments)):
        pbs_script_content += f"$tmux wait -S ping_${{session}}__{i}_{0}\n"
    pbs_script_content += '\n'
    # Wait for all the jobs to finish
    for i in range(len(selected_experiments)):
        pbs_script_content += f"$tmux wait ping_${{session}}__{i}_{len(selected_experiments[i])}\n"

    # Generate the PBS script
    pbs_script = \
f"""#!/bin/bash

#PBS -l select=1:ncpus=10:mpiprocs=10:ngpus=1
#PBS -l walltime=24:00:00
#PBS -j oe
#PBS -o /work/arosasco/diffusion_policy_og/.bulb/pbs_out.txt
#PBS -N {input_indices.replace(',', '-').replace(':', '_')}
#PBS -q gpu

set -e  # Exit immediately if a command exits with a non-zero status.
set -o pipefail  # Return value of a pipeline is the value of the last command to exit with a non-zero status, or zero if all commands exit successfully.
set -u  # Treat unset variables as an error when substituting.

{pbs_script_content}

tail -f /dev/null
"""

    # Write the PBS script to a file
    with open(pbs_output_file, 'w') as pbs_file:
        pbs_file.write(pbs_script)

    # Run the PBS script using qsubdd
    try:
        subprocess.run(["qsub", pbs_output_file], check=True)
        print(f"PBS script {pbs_output_file} submitted successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error submitting PBS script: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main(sys.argv)
