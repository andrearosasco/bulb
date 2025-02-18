

from pathlib import Path
import shutil
from typing import Literal
import os
import tempfile
import subprocess
from contextlib import contextmanager



@contextmanager
def temporary_index_file():
    """Context manager to temporarily set and restore the GIT_INDEX_FILE environment variable."""
    temp_index = tempfile.mktemp()
    original_index = os.environ.get('GIT_INDEX_FILE')
    
    try:
        os.environ['GIT_INDEX_FILE'] = temp_index
        yield temp_index
    finally:
        if os.path.exists(temp_index):
            os.unlink(temp_index)
        if original_index:
            os.environ['GIT_INDEX_FILE'] = original_index
        elif 'GIT_INDEX_FILE' in os.environ:
            del os.environ['GIT_INDEX_FILE']

def run_git_command(*args, cwd=None):
    """Run a Git command and return its output."""
    result = subprocess.run(args, check=True, text=True, capture_output=True, cwd=cwd)
    return result.stdout.strip()

def commit_to_ref(ref_name, commit_message):
    """
    Create a new commit from unstaged changes and update the given reference.
    Returns the commit hash.
    """
    with temporary_index_file():
        # Read the current HEAD into the temporary index
        run_git_command('git', 'read-tree', 'HEAD')
        
        # Get the list of modified files
        modified_files = run_git_command('git', 'diff', '--name-only').splitlines()
        
        if modified_files:
            # Add modified files to the temporary index
            run_git_command('git', 'add', *modified_files)
        
        # Write the tree object and get its ID
        tree_id = run_git_command('git', 'write-tree')
        
        # Get the current HEAD commit hash
        head_commit = run_git_command('git', 'rev-parse', 'HEAD')
        
        # Create a new commit from the tree and HEAD commit
        new_commit = run_git_command(
            'git', 'commit-tree', '-p', head_commit, '-m', commit_message, tree_id
        )
        
        # Update the reference to point to the new commit
        run_git_command('git', 'update-ref', ref_name, new_commit)
        
        return new_commit

def push_ref(ref_name, remote="origin"):
    """
    Push the given reference to the specified remote repository.
    """
    run_git_command('git', 'push', remote, ref_name)

def clone_repo(repo_url, clone_dir):
    """Clone a Git repository to the specified directory."""
    if os.path.exists(clone_dir):
        print(f"Directory {clone_dir} already exists.")
        return
    run_git_command('git', 'clone', repo_url, clone_dir)

def fetch_ref(clone_dir, ref_name):
    """Fetch a specific reference from the remote repository."""
    run_git_command('git', 'fetch', 'origin', f"{ref_name}:{ref_name}", cwd=clone_dir)

def checkout_ref(clone_dir, ref_name):
    """Checkout to the specified reference."""
    run_git_command('git', 'checkout', ref_name, cwd=clone_dir)