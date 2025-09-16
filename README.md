# Copy-Cat

Copy-Cat is a Python-based tool to migrate file changes between Git repositories with precision. It identifies the exact file modifications from a specified commit in a source repository and replicates them into a target repository branch. It supports added, modified, and deleted files, ensuring a seamless migration while keeping changes staged for manual review and commit.

## How It Works

The script operates in a few simple steps:
1.  **Load Configuration**: Reads the source repository path, target repository path, source commit SHA, and target branch from the `repo_migrator_config.json` file.
2.  **Prepare Repositories**: Initializes the source repository and checks out the specified target branch in the target repository. If the target branch doesn't exist, it creates a new one.
3.  **Detect Changes**: Uses `git diff-tree` to get a list of all files that were added, modified, or deleted in the specified source commit.
4.  **Migrate Files**:
    *   For **added** and **modified** files, it extracts the file content from the source commit and writes it to the corresponding path in the target repository.
    *   For **deleted** files, it removes the file from the target repository.
5.  **Stage Changes**: All migrated changes (additions, modifications, and deletions) are staged in the target repository using `git add` and `git rm`. The script does **not** commit the changes, allowing for a final review.

## Prerequisites

*   Python 3.x
*   Git command-line tool

## Setup and Configuration

1.  **Clone the repository:**
    ```sh
    git clone https://github.com/jerusheya/copy-cat.git
    cd copy-cat
    ```
2.  **Install dependencies:**
    The script requires the `GitPython` library.
    ```sh
    pip install GitPython
    ```
3.  **Configure the script:**
    Before running, you must update the hardcoded configuration path inside the `sync-changes/migrate_changes.py` file. Change this line to the absolute path of your `repo_migrator_config.json` file:
    ```python
    CONFIG_PATH = "/path/to/your/copy-cat/sync-changes/repo_migrator_config.json"
    ```
4.  **Edit the configuration file:**
    Modify `sync-changes/repo_migrator_config.json` with your repository details:

    *   `default_source_repo`: The absolute local path to the source Git repository.
    *   `default_target_repo`: The absolute local path to the target Git repository where changes will be applied.
    *   `source.commit`: The full SHA of the commit in the source repository whose changes you want to migrate.
    *   `target.branch`: The name of the branch in the target repository to apply the changes to. The script will create this branch if it does not exist.

    **Example `repo_migrator_config.json`:**
    ```json
      {
        "default_source_repo": "/Users/jejohnson/Documents/Apps/salesforce-connector-app-desk",
        "default_target_repo": "/Users/jejohnson/Documents/Apps/azure-connector-app-desk",
        "base_branch": "main",
        "migration_mode": "commit_to_local",
        "source": {
          "type": "commit",
          "branch": "security-issue-2",
          "commit": "71fdabb887266da95af94c7a263fec85faa346ac"
        },
        "target": {
          "type": "local",
          "branch": "security-issue"
        }
      }
    ```

## Usage

Once the setup and configuration are complete, run the script from the root directory of the `copy-cat` project:

```sh
python sync-changes/migrate_changes.py
```

The script will log its progress to the console, indicating which files are being copied, deleted, or skipped.

### Post-Migration Steps

After the script finishes, the changes are staged but **not committed** in the target repository.

1.  Navigate to your target repository:
    ```sh
    cd /path/to/your/default_target_repo
    ```
2.  Review the staged changes:
    ```sh
    git status
    git diff --staged
    ```
3.  If the changes are correct, commit them:
    ```sh
    git commit -m "Migrate changes from source repository"
