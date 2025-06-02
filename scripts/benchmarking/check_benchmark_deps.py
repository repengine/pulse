"""
Check if all dependencies for the retrodiction benchmarking are available.
"""

import importlib
import sys
import os
from pathlib import Path

# Add the project root to Python path so we can import local modules
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

required_packages = [
    ("cProfile", "Part of Python standard library for profiling"),
    ("pstats", "Part of Python standard library for profiling"),
    ("pandas", "For data manipulation and handling"),
    ("numpy", "For numerical operations"),
    ("recursive_training.parallel_trainer", "Pulse's parallel training module"),
    ("recursive_training.data.data_store", "Pulse's data store"),
    ("recursive_training.metrics.metrics_store", "Pulse's metrics store"),
    (
        "recursive_training.advanced_metrics.retrodiction_curriculum",
        "Pulse's retrodiction curriculum",
    ),
    ("analytics.optimized_trust_tracker", "Pulse's optimized trust tracker"),
    ("causal_model.optimized_discovery", "Pulse's optimized causal discovery"),
]

optional_packages = [("psutil", "For system information collection")]

missing_required = []
missing_optional = []

print("Checking required packages...")
for package, description in required_packages:
    try:
        importlib.import_module(package)
        print(f"✅ {package}: Available")
    except ImportError:
        print(f"❌ {package}: Missing - {description}")
        missing_required.append(package)

print("\nChecking optional packages...")
for package, description in optional_packages:
    try:
        importlib.import_module(package)
        print(f"✅ {package}: Available")
    except ImportError:
        print(f"⚠️ {package}: Missing - {description}")
        missing_optional.append(package)

if missing_required:
    print(
        "\n❌ Some required packages are missing. The benchmark may not run correctly."
    )
    print("Missing required packages:", missing_required)
    sys.exit(1)
elif missing_optional:
    print(
        "\n⚠️ All required packages are available, but some optional packages are missing."
    )
    print("Missing optional packages:", missing_optional)
    print("The benchmark will run with reduced functionality.")
    print("You can run the benchmark with: python benchmark_retrodiction.py")
else:
    print("\n✅ All required and optional packages are available.")
    print("You can run the benchmark with: python benchmark_retrodiction.py")
