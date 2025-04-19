import os
import shutil
import re

# Canonical locations for key files (extend as needed)
CANONICAL_PATHS = {
    "log_utils.py": "utils",
    "error_utils.py": "utils",
    "performance_utils.py": "utils",
    "pulse_shell_autohook.py": "dev_tools",
    "pulse_scan_hooks.py": "dev_tools",
    "hook_utils.py": "dev_tools",
    "module_dependency_map.py": "dev_tools",
    "pulse_prompt_logger.py": "operator_interface",
    "digest_exporter.py": "foresight_architecture",
    "digest_logger.py": "foresight_architecture",
    # ...add more as needed...
}

# Directories that should always have __init__.py
PACKAGE_DIRS = [
    "core", "utils", "dev_tools", "simulation_engine", "simulation_engine/rules",
    "forecast_engine", "forecast_output", "foresight_architecture", "memory",
    "symbolic_system", "capital_engine", "diagnostics", "operator_interface", "tests"
]

# Quarantine directory
QUARANTINE_DIR = "quarantine"

def ensure_init_py():
    for pkg in PACKAGE_DIRS:
        pkg_path = os.path.join(os.getcwd(), pkg)
        if os.path.isdir(pkg_path):
            init_path = os.path.join(pkg_path, "__init__.py")
            if not os.path.exists(init_path):
                with open(init_path, "w", encoding="utf-8") as f:
                    f.write("# Automatically created __init__.py\n")

def move_to_canonical():
    for fname, target_dir in CANONICAL_PATHS.items():
        for root, _, files in os.walk("."):
            if fname in files:
                src = os.path.join(root, fname)
                dest_dir = os.path.join(".", target_dir)
                dest = os.path.join(dest_dir, fname)
                if os.path.abspath(src) != os.path.abspath(dest):
                    os.makedirs(dest_dir, exist_ok=True)
                    if os.path.exists(dest):
                        # Quarantine duplicate
                        os.makedirs(QUARANTINE_DIR, exist_ok=True)
                        shutil.move(src, os.path.join(QUARANTINE_DIR, fname))
                        print(f"Quarantined duplicate: {src}")
                    else:
                        shutil.move(src, dest)
                        print(f"Moved {src} -> {dest}")

def update_imports():
    # Map of old import -> new import
    import_map = {
        r"from log_utils import": "from utils.log_utils import",
        r"from error_utils import": "from utils.error_utils import",
        r"from performance_utils import": "from utils.performance_utils import",
        r"from digest_exporter import": "from foresight_architecture.digest_exporter import",
        r"from digest_logger import": "from foresight_architecture.digest_logger import",
        r"from pulse_prompt_logger import": "from operator_interface.pulse_prompt_logger import",
        # ...add more as needed...
    }
    for root, _, files in os.walk("."):
        for fname in files:
            if fname.endswith(".py") and not fname.startswith("__"):
                fpath = os.path.join(root, fname)
                with open(fpath, "r", encoding="utf-8") as f:
                    content = f.read()
                orig_content = content
                for old, new in import_map.items():
                    content = re.sub(old, new, content)
                if content != orig_content:
                    with open(fpath, "w", encoding="utf-8") as f:
                        f.write(content)
                    print(f"Updated imports in {fpath}")

def main():
    ensure_init_py()
    move_to_canonical()
    update_imports()
    print("✅ Structure automation complete.")

if __name__ == "__main__":
    main()