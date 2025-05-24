import os
import shutil


def delete_pycache_dirs(root_dir):
    """
    Recursively find and delete all __pycache__ directories under root_dir.

    Args:
        root_dir (str): The root directory to start searching from.
    """
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Copy the list to avoid modifying while iterating
        for dirname in list(dirnames):
            if dirname == "__pycache__":
                pycache_dir = os.path.join(dirpath, dirname)
                print(f"Deleting: {pycache_dir}")
                shutil.rmtree(pycache_dir)
                # Remove from dirnames so os.walk does not visit it
                dirnames.remove(dirname)


if __name__ == "__main__":
    # Delete all __pycache__ dirs from the current directory down
    delete_pycache_dirs(os.getcwd())
