from git import Repo
from git.exc import InvalidGitRepositoryError, NoSuchPathError
import os
import subprocess
import json

CONFIG_PATH = "/Users/jejohnson/Documents/personal_projects/copy-cat/sync-changes/repo_migrator_config.json"

# ---------------------------
# Load configuration
# ---------------------------
def load_config():
    if not os.path.exists(CONFIG_PATH):
        raise FileNotFoundError(f"Config file not found at {CONFIG_PATH}")
    with open(CONFIG_PATH, 'r') as f:
        return json.load(f)

# ---------------------------
# Checkout or create branch (handles remote branches)
# ---------------------------
def checkout_or_create_branch(repo_path, branch_name):
    if not os.path.exists(repo_path):
        print(f"📂 Target repo path does not exist. Creating it: {repo_path}")
        os.makedirs(repo_path, exist_ok=True)

    try:
        repo = Repo(repo_path)
    except (InvalidGitRepositoryError, NoSuchPathError):
        print(f"🔹 No such repo found at {repo_path}")

    # Fetch latest remote branches if any
    if repo.remotes:
        for remote in repo.remotes:
            remote.fetch()

    # Determine if branch exists locally or remotely
    if branch_name in repo.heads:
        print(f"✅ Found branch '{branch_name}' locally. Checking out...")
        repo.git.checkout(branch_name, force=True)
    elif f"origin/{branch_name}" in repo.git.branch('-r'):
        print(f"✅ Found branch '{branch_name}' on remote. Checking out locally...")
        repo.git.checkout('-b', branch_name, f"origin/{branch_name}")
    else:
        print(f"🔹 Branch '{branch_name}' not found. Creating it...")
        repo.git.checkout('-b', branch_name)

    print("🔹 Target repo current branch:", repo.active_branch)
    return repo

# ---------------------------
# Detect files in a commit
# ---------------------------
def get_commit_changes(repo_path, commit_sha):
    """
    Returns list of (file_path, status) from commit.
    Status: A (added), M (modified), D (deleted)
    """
    cmd = ['git', 'diff-tree', '--no-commit-id', '--name-status', '-r', commit_sha]
    output = subprocess.check_output(cmd, cwd=repo_path).decode('utf-8').strip()

    changes = []
    for line in output.splitlines():
        parts = line.split('\t')
        if len(parts) == 2:
            status, path = parts
            changes.append((path, status))
    return changes

# ---------------------------
# Get file content from a commit
# ---------------------------
def get_file_from_commit(repo_path, commit, file_path):
    try:
        return subprocess.check_output(
            ['git', 'show', f'{commit}:{file_path}'],
            cwd=repo_path
        ).decode('utf-8')
    except subprocess.CalledProcessError:
        return None

# ---------------------------
# Copy file from commit to target
# ---------------------------
def copy_file_from_commit(repo_path, commit_sha, file_path, target_full_path):
    file_content = get_file_from_commit(repo_path, commit_sha, file_path)
    if file_content is None:
        print(f"⚠️ File not found in commit {commit_sha}: {file_path}")
        return False

    os.makedirs(os.path.dirname(target_full_path), exist_ok=True)
    with open(target_full_path, 'w') as f:
        f.write(file_content)

    if os.path.exists(target_full_path):
        print(f"✅ Verified: {target_full_path} exists on disk")
    else:
        print(f"❌ ERROR: {target_full_path} was NOT written!")

    return True

# ---------------------------
# Main migration function
# ---------------------------
def migrate_changes():
    config = load_config()

    source_repo_path = config['default_source_repo']
    target_repo_path = config['default_target_repo']
    migration_mode = config.get('migration_mode', 'commit_to_local')
    source_info = config['source']
    target_info = config['target']

    # Prepare repos
    source_repo = Repo(source_repo_path)
    target_repo = checkout_or_create_branch(target_repo_path, target_info['branch'])

    if migration_mode == "commit_to_local":
        commit_sha = source_info['commit']
        changes = get_commit_changes(source_repo_path, commit_sha)

        if not changes:
            print("✅ No changes found in the specified commit.")
            return

        print(f"\n📂 Files to migrate from commit {commit_sha}: {[c[0] for c in changes]}")

        for file_path, status in changes:
            target_file_path = os.path.join(target_repo_path, file_path)
            rel_path = os.path.relpath(target_file_path, target_repo_path)

            if status == 'D':
                if os.path.exists(target_file_path):
                    os.remove(target_file_path)
                    target_repo.git.rm(rel_path, force=True)
                    print(f"🗑️ Deleted: {file_path}")
                else:
                    print(f"⚠️ Skipped deletion (file not found locally): {file_path}")
                continue

            if copy_file_from_commit(source_repo_path, commit_sha, file_path, target_file_path):
                target_repo.git.add(rel_path)
                print(f"📄 Copied: {file_path}")
            else:
                print(f"⚠️ Failed to copy: {file_path}")

    print("\n🎉 Migration complete!")
    print("⚠️ NOTE: Changes are staged but NOT committed. Review before committing.")

# ---------------------------
# Entry point
# ---------------------------
if __name__ == "__main__":
    migrate_changes()
