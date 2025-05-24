# GitHub Large Repository Fix Plan

## 1. Problem Statement

The Git repository has exceeded 2GB in size, which is GitHub's recommended limit for a single push and can lead to push failures or performance issues. This plan outlines strategies to reduce the repository size and enable successful pushes to GitHub.

## 2. Strategies to Address Large Repository Size

### 2.1. Identifying Large Files in Git History

Before deciding on a solution, it's crucial to identify which files or types of files are contributing most to the repository's size.

*   **Using `git rev-list --objects --all`:**
    This command lists all objects in the Git repository. It can be combined with `git cat-file -s` to get their sizes.
    ```bash
    # List top 10 largest objects
    git rev-list --objects --all | \
      git cat-file --batch-check='%(objectname) %(objecttype) %(objectsize) %(rest)' | \
      sed -n 's/^[^ ]* blob //p' | \
      sort --numeric-sort --key=1 -r | \
      head -n 10
    ```
    This helps identify individual large blobs, but not necessarily the files associated with them directly in all commits.

*   **Using `git-filter-repo --analyze`:**
    `git-filter-repo` is a powerful tool for rewriting Git history. Its analysis feature provides a detailed report on repository contents.
    ```bash
    # Install git-filter-repo if not already installed (e.g., via pip)
    # pip install git-filter-repo

    # Run analysis
    git-filter-repo --analyze
    # The report will be generated in .git/filter-repo/analysis/
    ```
    This report includes `blob-shas-and-paths.txt` (mapping blob SHAs to paths) and `path-sizes.txt` (listing largest paths).

*   **BFG Repo-Cleaner (Analysis):**
    The BFG Repo-Cleaner is another tool designed to remove large or unwanted files from Git history. It can also be used for analysis.
    ```bash
    # Download BFG (e.g., bfg.jar)
    # java -jar bfg.jar --strip-blobs-bigger-than 1M --no-blob-protection my-repo.git
    ```
    While primarily a cleaning tool, its dry-run output can help identify large files.

### 2.2. Removing Large Files from Git History

If large files are not essential or were added by mistake, they can be removed from the entire Git history. **Warning:** This rewrites history and requires coordination with all collaborators. Always back up your repository before attempting history rewriting.

*   **Using `git filter-repo`:**
    This is the currently recommended tool by Git for history rewriting.
    ```bash
    # Example: Remove all files larger than 100MB
    git filter-repo --strip-blobs-bigger-than 100M

    # Example: Remove specific large files by path
    git filter-repo --invert-paths --path path/to/large-file.zip --path another/large-file.dat
    ```
    After running `git filter-repo`, you'll need to force push the changes. Collaborators will need to re-clone or carefully reset their local repositories.

*   **BFG Repo-Cleaner:**
    The BFG is simpler for some common use cases.
    ```bash
    # Example: Remove all files larger than 50MB
    java -jar bfg.jar --strip-blobs-bigger-than 50M my-repo.git

    # Example: Remove all files named 'big.jar' or 'huge.zip'
    java -jar bfg.jar --delete-files "{big.jar,*.zip}" my-repo.git
    ```
    BFG automatically cleans up and runs `git gc`. Like `git filter-repo`, it rewrites history.

### 2.3. Using Git LFS (Large File Storage)

Git LFS is an extension for Git that replaces large files with text pointers inside Git, while storing the file contents on a remote server like GitHub LFS or a self-hosted LFS server. This is suitable for files that need to be versioned but are too large for the main repository.

*   **Installation:**
    Install the Git LFS client locally.
    ```bash
    # On macOS (using Homebrew)
    brew install git-lfs

    # On Windows (download installer from git-lfs.github.com)
    # On Linux (package manager, e.g., apt-get install git-lfs)
    ```
    Initialize LFS for the repository (run once per repository):
    ```bash
    git lfs install
    ```

*   **Tracking Files:**
    Tell Git LFS which files to track. This creates/updates the `.gitattributes` file.
    ```bash
    # Track all .psd files
    git lfs track "*.psd"

    # Track a specific large file
    git lfs track "videos/large-video.mp4"
    ```
    Commit the `.gitattributes` file:
    ```bash
    git add .gitattributes
    git commit -m "Track large files with Git LFS"
    ```

*   **Migrating Existing Files:**
    To move files already committed in history to LFS, use `git lfs migrate`. **Warning:** This also rewrites history.
    ```bash
    # Migrate all files matching a pattern across all history
    git lfs migrate import --everything --include="*.dat,*.iso"

    # For a more targeted approach (e.g., only files larger than 10MB)
    # This often requires scripting or using git-filter-repo in conjunction with LFS commands.
    # A common pattern is to first identify large files, then use `git filter-repo` to rewrite them as LFS pointers.
    # Example using git filter-repo to prepare for LFS (advanced):
    # git filter-repo --blob-callback '
    #   if blob.data.startswith(b"version https://git-lfs.github.com/spec/v1"):
    #     return  # Skip already LFS pointers
    #   if len(blob.data) > 10*1024*1024: # 10MB
    #     # Create LFS pointer file content
    #     sha256 = hashlib.sha256(blob.data).hexdigest()
    #     pointer_content = f"version https://git-lfs.github.com/spec/v1\noid sha256:{sha256}\nsize {len(blob.data)}\n".encode()
    #     blob.data = pointer_content
    # ' --path-glob '*.iso' --path-glob '*.dat'
    ```
    After migration, force push the changes.

## 3. Proposed High-Level Plan

1.  **BACKUP REPOSITORY:**
    *   **Action:** Create a full, mirrored clone of the repository.
        ```bash
        git clone --mirror git@github.com:user/repo.git repo.bak
        cd repo.bak
        # Or simply copy the .git folder if working locally
        ```
    *   **Importance:** Critical for recovery in case of errors during history rewriting.

2.  **ANALYZE REPOSITORY SIZE:**
    *   **Action:** Use `git-filter-repo --analyze` or `git rev-list --objects --all` with scripting to identify the largest files and directories.
    *   **Goal:** Understand what is consuming space.

3.  **DECISION POINT: Remove Files vs. Use Git LFS:**
    *   **Consider:**
        *   Are the large files binary assets that don't diff well (e.g., compiled executables, videos, large datasets, design files)? **Favors Git LFS.**
        *   Were the large files added by mistake and are no longer needed? **Favors Removal.**
        *   Does the team frequently update these large files? **Favors Git LFS.**
        *   Are there concerns about LFS storage quotas or costs? **May favor Removal if feasible.**

4.  **EXECUTE CHOSEN STRATEGY:**

    *   **Option A: Remove Large Files Permanently**
        1.  **Tool Selection:** Prefer `git filter-repo`.
        2.  **Identify Files:** Based on analysis, list files/patterns to remove.
        3.  **Rewrite History:**
            ```bash
            # Example:
            git filter-repo --strip-blobs-bigger-than 50M --force
            # OR
            git filter-repo --invert-paths --path path/to/remove --force
            ```
        4.  **Cleanup Git:**
            ```bash
            git reflog expire --expire=now --all
            git gc --prune=now --aggressive
            ```

    *   **Option B: Implement Git LFS**
        1.  **Install LFS Client:** Ensure all collaborators install it.
        2.  **Initialize LFS:** `git lfs install` (in the working repository).
        3.  **Migrate Existing Data (if applicable):**
            ```bash
            # Example:
            git lfs migrate import --everything --include="*.psd,*.dat"
            # Ensure .gitattributes is updated and committed by migrate.
            ```
            If `migrate` is not sufficient, use `git filter-repo` to rewrite history and convert large files to LFS pointers.
        4.  **Track New Files:** Add patterns to `.gitattributes` for future large files.
            ```bash
            git lfs track "*.new_large_ext"
            git add .gitattributes
            git commit -m "Update LFS tracking rules"
            ```

5.  **TEAM COORDINATION (Crucial for History Rewriting):**
    *   **Communicate:** Inform all collaborators *before* force pushing.
    *   **Instructions for Collaborators:**
        *   If they don't have unpushed changes:
            ```bash
            git fetch origin
            git reset --hard origin/main # Or relevant branch
            ```
        *   If they have unpushed changes: Rebase their changes onto the new history (can be complex). Often easier to back up their changes, reset, then re-apply.
            ```bash
            # Backup branch
            git checkout -b my-backup-branch
            # Reset to new history
            git checkout main # Or relevant branch
            git fetch origin
            git reset --hard origin/main
            # Re-apply changes (e.g., cherry-pick or rebase)
            git cherry-pick <commit-hash-from-backup-branch>
            # OR
            git rebase origin/main my-feature-branch # After fetching new main
            ```

6.  **FORCE PUSH CHANGES:**
    *   **Action:**
        ```bash
        git push origin --force --all
        git push origin --force --tags
        ```
    *   **Note:** This overwrites the remote history.

7.  **VERIFY:**
    *   **Action:** Check repository size on GitHub. Attempt a normal push/pull cycle.
    *   **Goal:** Confirm the issue is resolved.

8.  **CLEANUP (Optional):**
    *   Remove the backup repository once confident.

## 4. Potential Risks

*   **Data Loss:** If backups are not made or are faulty, and history rewriting goes wrong.
*   **Team Disruption:** Rewriting history requires all collaborators to update their local repositories. Miscommunication or incorrect procedures can lead to lost work or complex merge conflicts.
*   **Broken Builds/CI:** If CI/CD systems are not updated to handle new history or LFS.
*   **LFS Costs/Limits:** GitHub and other LFS providers have storage and bandwidth quotas. Exceeding these can incur costs.
*   **LFS Complexity:** Adds another layer to the Git workflow; team members need to understand how LFS works.
*   **Irreversible Changes:** While backups help, history rewriting is a destructive operation on the repository's commit graph.

## 5. Prerequisites

*   **Full Repository Backup:** A `--mirror` clone is recommended.
*   **Tool Installation:**
    *   `git-filter-repo` (if chosen for removal/migration).
    *   BFG Repo-Cleaner (if chosen).
    *   Git LFS client (if chosen, for all collaborators).
*   **Administrative Access:** To the GitHub repository to adjust settings if needed (e.g., LFS billing).
*   **Team Agreement & Coordination Plan:** Essential before rewriting history.
*   **Understanding of Git Internals:** At least one team member should have a good grasp of Git history, rewriting, and LFS concepts.

## 6. Conclusion

Addressing a large Git repository requires careful planning and execution. The choice between removing files and using Git LFS depends on the nature of the large files and team workflows. Thorough analysis, robust backups, and clear team communication are paramount to a successful resolution.
## 7. Verification

Verified by: Verify Mode
Date: May 21, 2025
Outcome: Plan confirmed as complete and logical. All key elements (problem statement, methods for identification, remediation strategies, step-by-step plan, risks, and prerequisites) are present and well-defined.
## 8. Repository Analysis (git-filter-repo)

**Date:** May 21, 2025
**Action Taken:** Executed `git-filter-repo --analyze` to identify large files and overall repository structure.
**Summary of Findings:**
*   Analysis reports generated in `.git/filter-repo/analysis/`
*   The command output indicated that rename detection was skipped due to too many files, suggesting a complex history.
**Next Steps:** Review the generated analysis reports in `.git/filter-repo/analysis/` to identify specific large files and decide on a remediation strategy (removal or Git LFS).
### 8.1 Locating Analysis Files

**Date:** May 21, 2025
**Action Taken:** User reported difficulty finding analysis files. Executed `dir .git\\filter-repo\\analysis` to list contents of the expected directory.
**Output/Observed Files:**
*   blob-shas-and-paths.txt
*   directories-all-sizes.txt
*   directories-deleted-sizes.txt
*   extensions-all-sizes.txt
*   extensions-deleted-sizes.txt
*   path-all-sizes.txt
*   path-deleted-sizes.txt
*   README
*   renames.txt
**Next Steps:** Based on the output, guide the user to review the listed files or troubleshoot further if the files are still not found.
### 8.2 Summary of Largest Files/Blobs from Analysis Reports

**Date:** May 21, 2025
**Action Taken:** Read `path-all-sizes.txt` and `blob-shas-and-paths.txt` (as `blob-all-sizes.txt` was not found) because the user was unable to open them.
**Largest Paths (from `path-all-sizes.txt`):**
*   `data/manual_bulk_data/Zillow/ZILLOW_DATA_962c837a6ccefddddf190101e0bafdaf.zip` - 1634.68 MB
*   `chatmode/vector_store/codebase.faiss` - 109.19 MB
*   `data/manual_bulk_data/WB_DATA_d950d0cd269a601150c0afd03b234ee2.zip` - 96.96 MB
*   `data/manual_bulk_data/QDL_JODI_79de9c79555cfb80e0047a11fce1a958.zip` - 74.37 MB
*   `data/manual_bulk_data/CFTC/QDL_LFON_ee0612663634d213cdd7a941ca16c4b0.zip` - 64.14 MB
*   `data/manual_bulk_data/CFTC/QDL_FON_50ecfe163057383d2412f0c40931239e.zip` - 56.19 MB
*   `data/manual_bulk_data/CFTC/QDL_FCR_2fe8499abfbd15c8f4d4cb7072a708e3.zip` - 27.40 MB
*   `data/manual_bulk_data/QDL_BITFINEX_bd501c887fbc1cc545f11778912a9118.zip` - 20.28 MB
*   `chatmode/vector_store/codebase_metadata.pkl` - 6.58 MB
*   `data/manual_bulk_data/WASDE/WASDE_DATA_0cdaff592f19dc15ab6e8eba9102bc11.zip` - 6.03 MB
*   `logs/pulse_learning_log.jsonl` - 5.44 MB
*   `data/manual_bulk_data/QDL_ODA_5ece5fc323f5515a20a4c38442a04359.zip` - 2.44 MB
*   `data/recursive_training/indices/main_indices.json` - 1.68 MB
*   `data/manual_bulk_data/Zillow/ZILLOW_REGIONS_1a51d107db038a83ac171d604cb48d5b.zip` - 1.60 MB
*   `data/manual_bulk_data/QDL_BCHAIN_503d04810b3c433a6f9acae5067f68dc.zip` - 1.10 MB

**Largest Blobs (from `blob-shas-and-paths.txt`):**
*   `bf2f220729fc298f14a7bf44e0882b8cba6fe773` - 1634.68 MB
*   `ce79d47eb533fd360814edc2239b00209e404cdf` - 109.19 MB
*   `9a113138e7d4224da8c491d0160a810205d35c89` - 96.96 MB
*   `0d82b32189a5c4571bafa6376d2b8fcf4d4469a5` - 74.37 MB
*   `e4597126573594a54810a7504394a14c9a2b0d29` - 64.14 MB
*   `f7da1277a28ba9c245d26d351513ca7b94bc2c8d` - 56.19 MB
*   `4e0609438cfafbec26188f4d89d9ed1aac6a2e0a` - 27.40 MB
*   `b5ff0337e3707aeb22a56945a0be6c1eace8eb26` - 20.28 MB
*   `efad0365f30b4c47177474172a6d2b319a22ccc7` - 6.58 MB
*   `abb8e2c2ca42d2659339fa05807446c62061f8ef` - 6.03 MB
*   `b6adf8f8834a782142c67cc2766afff407970aea` - 2.44 MB
*   `c0fcb081cf93ad80851289164d56c7cfda3d8ca1` - 1.61 MB
*   `892bb3e0ae621aaf87fc62ab3c7826d2ba2e09c9` - 1.60 MB
*   `e0df08527c196e142861fcedfccf90c53fe0a83f` - 1.10 MB
*   `b7d3a1b130e3cb55972570793e8324a3071d7efc` - 0.98 MB

**Next Steps:** Based on this summary, decide which files/blobs to target for removal or Git LFS.
## 9. Ignoring and Removing Large Files/Folders

**Date:** May 21, 2025
**Action Taken:**
1.  Added `data/` and `chatmode/vector_store/codebase.faiss` to `.gitignore`.
2.  Committed `.gitignore` changes.
3.  Executed `git filter-repo --path data/ --path chatmode/vector_store/codebase.faiss --invert-paths --force` to remove these paths from Git history.

**Files/Folders Targeted:**
*   `data/` (entire directory)
*   `chatmode/vector_store/codebase.faiss`

**Outcome:** History rewritten to exclude the specified paths. `.gitignore` updated to prevent future tracking.
**Next Steps:** Verify repository size reduction, clean up old refs (`git reflog expire --expire=now --all && git gc --prune=now --aggressive`), and attempt to push to GitHub.
### 9.1 Verifying Local Repository Object Size

**Date:** May 21, 2025
**Action Taken:** Executed `git count-objects -vH` to check the local repository's object storage size after filtering.
**Output (`git count-objects -vH`):**
```
count: 0
size: 0 bytes
in-pack: 35934
packs: 1
size-pack: 27.72 MiB
prune-packable: 0
garbage: 0
size-garbage: 0 bytes
```
**Interpretation:** This output shows the current count of various Git objects and their total disk size locally. The 'size-pack' value (27.72 MiB) is particularly relevant as it indicates the size of compressed objects.
**Next Steps:** Proceed with `git gc` to further optimize, then attempt to push to GitHub.
### 9.2 Checking Remote Configuration

**Date:** May 21, 2025
**Action Taken:** User encountered push error (`fatal: 'origin' does not appear to be a git repository`). Executed `git remote -v` to check remote 'origin' configuration.
**Output (`git remote -v`):**
```
mcp-tmphttps://github.com/modelcontextprotocol/servers.git (fetch)
mcp-tmp https://github.com/modelcontextprotocol/servers.git (push)
```
**(Note: Initial output line `git pu^CX` appears to be a user interruption and is omitted here.)**

**Interpretation:** No remote named 'origin' is configured. A remote named 'mcp-tmp' exists, pointing to `https://github.com/modelcontextprotocol/servers.git`. The absence of an 'origin' remote is the cause of the push error.
**Next Steps:** Add a new remote named 'origin' pointing to the correct repository URL for this project. Alternatively, if 'mcp-tmp' is the intended primary remote for this project, it should be renamed to 'origin' using `git remote rename mcp-tmp origin`.

### 9.3 Preparing to Remove 'mcp-tmp' Remote

**Date:** May 21, 2025
**Action Taken:** Read the current `.git/config` file to understand the existing remote configuration before attempting to remove the `mcp-tmp` remote.
**Current `.git/config` Content:**
```
[core]
	repositoryformatversion = 0
	filemode = false
	bare = false
	logallrefupdates = true
	symlinks = false
	ignorecase = true
[remote "mcp-tmp"]
	url = https://github.com/modelcontextprotocol/servers.git
	fetch = +refs/heads/*:refs/remotes/mcp-tmp/*
[lfs]
	repositoryformatversion = 0
[lfs "https://github.com/repengine/Pulse.git/info/lfs"]
	access = basic
[branch "main"]
	vscode-merge-base = mcp-tmp/main
```

**Next Steps:** Modify the `.git/config` content to remove the `mcp-tmp` remote section and any references to it (like in `[branch "main"]`).
### 9.4 Removed 'mcp-tmp' Remote from .git/config

**Date:** May 21, 2025
**Action Taken:** Modified the `.git/config` file to remove the `[remote "mcp-tmp"]` section and the `vscode-merge-base = mcp-tmp/main` line from the `[branch "main"]` section.
**New `.git/config` Content:**
```
[core]
	repositoryformatversion = 0
	filemode = false
	bare = false
	logallrefupdates = true
	symlinks = false
	ignorecase = true
[lfs]
	repositoryformatversion = 0
[lfs "https://github.com/repengine/Pulse.git/info/lfs"]
	access = basic
[branch "main"]
```
**Next Steps:** Remind the user to disable SPARC MCP integration in IDE/project settings and set up the 'origin' remote.
## 10. Setting Up GitHub Remote and Pushing

**Date:** May 21, 2025
**Action Taken:**
1.  Added 'origin' remote pointing to `https://github.com/repengine/Pulse.git` using `git remote add origin https://github.com/repengine/Pulse.git`.
2.  Verified remote configuration using `git remote -v`.

**Output of `git remote -v` after adding origin:**
```
origin	https://github.com/repengine/Pulse.git (fetch)
origin	https://github.com/repengine/Pulse.git (push)
```
**Next Steps:** Clean up old Git references and force push to the new 'origin'.