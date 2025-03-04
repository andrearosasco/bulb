

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
    stdout = result.stdout.strip()
    print(stdout)
    return stdout

def commit_to_ref(ref_name, commit_message):
    """
    Create a new commit from unstaged changes and update the given reference.
    Returns the commit hash.
    """
    with temporary_index_file():
        # Read the current HEAD into the temporary index
        run_git_command('git', 'read-tree', 'HEAD')
        
        # Get the list of modified files
        modified_files = run_git_command('git', 'diff', '--name-only', 'HEAD').splitlines()
        
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
    run_git_command('git', 'clone', '--depth', '1', repo_url, clone_dir)

def fetch_ref(clone_dir, ref_name):
    """Fetch a specific reference from the remote repository."""
    run_git_command('git', 'fetch', '--unshallow', 'origin', f"{ref_name}:{ref_name}", cwd=clone_dir)

def checkout_ref(clone_dir, ref_name):
    """Checkout to the specified reference."""
    run_git_command('git', 'checkout', ref_name, cwd=clone_dir)


def git_pull(repo_path: str) -> bool:
    """
    Pull latest changes from remote repository.
    
    Args:
        repo_path: Path to the git repository
    
    Returns:
        Boolean indicating success or failure
    """
    if not os.path.exists(os.path.join(repo_path, '.git')):
        print(f"Error: {repo_path} is not a git repository")
        return False
    
    # Fetch latest changes
    run_git_command('git', 'fetch', 'origin', 'main', cwd=repo_path)
    # Pull changes
    run_git_command('git', 'pull', 'origin', 'main', cwd=repo_path)
    print("Successfully pulled latest changes")
    return True

def git_push(repo_path: str) -> bool:
    """
    Stage all changes, commit, and push to remote repository.
    
    Args:
        repo_path: Path to the git repository
        commit_message: Commit message
    
    Returns:
        Boolean indicating success or failure
    """
    if not os.path.exists(os.path.join(repo_path, '.git')):
        print(f"Error: {repo_path} is not a git repository")
        return False
    
    # Stage all changes
    run_git_command('git', 'add', '.', cwd = repo_path)
    # Commit changes
    run_git_command('git', 'commit', '-m', 'synching experiments', cwd = repo_path)
    # Push changes
    run_git_command('git', 'push', 'origin', 'main', cwd = repo_path)  
    print("Successfully pushed changes")
    return True
