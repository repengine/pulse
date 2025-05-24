#!/usr/bin/env python3
"""
Git repository cleanup script
This script helps clean up a Git repository by:
1. Creating a .gitattributes file for Git LFS (if needed)
2. Providing commands to clean up the repository history
"""

import os
import subprocess


def run_command(command, silent=False):
    """Run a system command and print the output if not silent"""
    if not silent:
        print(f"Running: {command}")

    try:
        result = subprocess.run(
            command, shell=True, check=True, text=True, capture_output=True
        )
        if not silent and result.stdout:
            print(result.stdout)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {command}")
        print(f"Error message: {e.stderr}")
        return None


def get_repo_size():
    """Get the size of the Git repository in MB"""
    # Check if .git directory exists
    if not os.path.isdir(".git"):
        print(
            "Not a Git repository. Run this script from the root of your Git repository."
        )
        return None

    # Get repository size using git count-objects
    result = run_command("git count-objects -v", silent=True)
    if not result:
        return None

    lines = result.strip().split("\n")
    size_in_kb = 0
    for line in lines:
        if line.startswith("size-pack:"):
            size_in_kb = int(line.split(":")[1].strip())
            break

    return size_in_kb / 1024  # Convert to MB


def suggest_lfs_setup():
    """Suggest Git LFS setup for specific file types"""
    print("\n--- GIT LFS SUGGESTIONS ---")
    print(
        "If your repository contains large binary files that you need to track, consider using Git LFS."
    )
    print("Here's a suggested .gitattributes file for common large file types:")

    gitattributes_content = """# Audio
*.mp3 filter=lfs diff=lfs merge=lfs -text
*.wav filter=lfs diff=lfs merge=lfs -text
*.ogg filter=lfs diff=lfs merge=lfs -text

# Video
*.mp4 filter=lfs diff=lfs merge=lfs -text
*.mov filter=lfs diff=lfs merge=lfs -text
*.avi filter=lfs diff=lfs merge=lfs -text
*.mkv filter=lfs diff=lfs merge=lfs -text

# Images
*.psd filter=lfs diff=lfs merge=lfs -text
*.ai filter=lfs diff=lfs merge=lfs -text
*.tif filter=lfs diff=lfs merge=lfs -text
*.tiff filter=lfs diff=lfs merge=lfs -text

# Archives
*.zip filter=lfs diff=lfs merge=lfs -text
*.rar filter=lfs diff=lfs merge=lfs -text
*.7z filter=lfs diff=lfs merge=lfs -text
*.tar.gz filter=lfs diff=lfs merge=lfs -text

# Data & Models
*.csv filter=lfs diff=lfs merge=lfs -text
*.parquet filter=lfs diff=lfs merge=lfs -text
*.pkl filter=lfs diff=lfs merge=lfs -text
*.h5 filter=lfs diff=lfs merge=lfs -text
*.hdf5 filter=lfs diff=lfs merge=lfs -text
*.npy filter=lfs diff=lfs merge=lfs -text
*.npz filter=lfs diff=lfs merge=lfs -text
*.bin filter=lfs diff=lfs merge=lfs -text
*.onnx filter=lfs diff=lfs merge=lfs -text
*.pt filter=lfs diff=lfs merge=lfs -text
*.pth filter=lfs diff=lfs merge=lfs -text
*.weights filter=lfs diff=lfs merge=lfs -text
"""

    print(gitattributes_content)
    print("To set up Git LFS, run the following commands:")
    print("  1. git lfs install")
    print("  2. Create .gitattributes with the content above")
    print("  3. git add .gitattributes")
    print("  4. git commit -m 'Set up Git LFS tracking'")
    print("  5. Continue with the repository cleanup steps below")
    print("\nNote: You'll need to install Git LFS first if you haven't already.")
    print("Windows: https://git-lfs.com/")
    print("macOS: brew install git-lfs")
    print("Linux: apt-get install git-lfs (or your distro's equivalent)")


def cleanup_instructions():
    """Print instructions for cleaning up the repository"""
    print("\n--- REPOSITORY CLEANUP STEPS ---")
    print("Warning: These steps modify your Git history. Make sure you have a backup!")
    print("Also ensure teammates are aware as these changes require a force push.")
    print("\nTo clean up your repository and reduce its size:")
    print("1. Make sure you've committed and pushed all your changes first")
    print(
        "2. Remove files from Git's history: Run this command to purge large files based on .gitignore:"
    )
    print(
        "   git filter-branch --index-filter 'git rm -rf --cached --ignore-unmatch $(git ls-files -ci --exclude-standard)' --prune-empty --tag-name-filter cat -- --all"
    )
    print("3. Clean up Git's internal files:")
    print("   git gc --aggressive --prune=now")
    print("4. Force push the changes (be careful!):")
    print("   git push origin --force --all")
    print("\nAlternative approach using BFG Repo-Cleaner (faster and easier):")
    print("1. Download BFG Repo-Cleaner: https://rtyley.github.io/bfg-repo-cleaner/")
    print("2. Make a fresh clone of your repository:")
    print("   git clone --mirror git@github.com:yourusername/yourrepo.git")
    print("3. Run BFG to remove large files:")
    print("   java -jar bfg-1.14.0.jar --strip-blobs-bigger-than 10M yourrepo.git")
    print("4. Clean up Git's internal files:")
    print(
        "   cd yourrepo.git && git reflog expire --expire=now --all && git gc --prune=now --aggressive"
    )
    print("5. Push the changes:")
    print("   git push")
    print("\nThis should significantly reduce your repository size.")


def main():
    repo_size = get_repo_size()
    if repo_size is None:
        return

    print(f"Current Git repository size: {repo_size:.2f} MB")

    if repo_size > 1000:  # More than 1GB
        print(f"WARNING: Your repository is over {repo_size / 1000:.2f} GB!")
        print("GitHub has a 2GB size limit. You need to reduce your repository size.")
    elif repo_size > 500:  # More than 500MB
        print("Your repository is quite large. Consider cleaning it up.")
    else:
        print(
            "Your repository size is reasonable, but cleaning can still be beneficial."
        )

    suggest_lfs_setup()
    cleanup_instructions()


if __name__ == "__main__":
    main()
