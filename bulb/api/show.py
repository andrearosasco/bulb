import os
import subprocess
import sys
from io import StringIO

# Configuration
PROJECT_DIR = "/work/arosasco/diffusion_policy_og"
DATABASE_FILE = os.path.join(PROJECT_DIR, ".bulb", "database.txt")

# Function to read and display experiment details
def display_experiment_details():
    output = StringIO()

    if not os.path.isfile(DATABASE_FILE):
        output.write(f"Database file not found at {DATABASE_FILE}.\n")
        return output.getvalue()

    output.write("Experiment Details:\n")
    output.write("-------------------\n")

    with open(DATABASE_FILE, 'r') as db_file:
        index = 1
        for line in db_file:
            line = line.strip()
            if not line:
                continue

            # Extract experiment name and log directory path
            parts = line.split(' : ')
            EXPERIMENT_NAME = parts[0]
            EXP_PATH = parts[1]

            # Calculate the relative path
            RELATIVE_PATH = os.path.relpath(os.path.dirname(EXP_PATH), PROJECT_DIR)

            if os.path.exists(EXP_PATH):
                EXISTS = ""
            else:
                EXISTS = " (Directory not found)"

            # Read the content of the status.txt file
            STATUS_FILE = os.path.join(EXP_PATH, ".bulb", "status.txt")
            if os.path.isfile(STATUS_FILE):
                with open(STATUS_FILE, 'r') as status_file:
                    STATUS_CONTENT = status_file.read().strip()
            else:
                STATUS_CONTENT = "Status file not found."

            # Read the content of the description.txt file and handle multi-line alignment
            COMMENT_FILE = os.path.join(EXP_PATH, ".bulb", "description.txt")
            if os.path.isfile(COMMENT_FILE):
                with open(COMMENT_FILE, 'r') as comment_file:
                    COMMENT_CONTENT = comment_file.read().strip()
                    COMMENT_CONTENT = "\n    ".join(COMMENT_CONTENT.splitlines())
            else:
                COMMENT_CONTENT = "Comment file not found."

            # Display experiment details
            output.write(f"[{index}] Experiment Name: {EXPERIMENT_NAME}{EXISTS}\n")
            output.write(f"    Path: {RELATIVE_PATH}\n")
            output.write(f"    Status: {STATUS_CONTENT}\n")
            output.write(f"    Comment: {COMMENT_CONTENT}\n\n")

            index += 1
    
    return output.getvalue()

# Main script execution
if __name__ == "__main__":
    details = display_experiment_details()
    
    # Use less to display the output
    pager = subprocess.Popen(['less'], stdin=subprocess.PIPE)
    try:
        pager.communicate(input=details.encode('utf-8'))
    except KeyboardInterrupt:
        pass
    pager.wait()
