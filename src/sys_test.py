"""
Consolidated system test runner.
Runs the full test suite under the tests/ directory using pytest.
"""

import os
import sys

# Remove current directory from sys.path to avoid local package shadowing of stdlib modules
# Remove current directory from sys.path to avoid local package shadowing of stdlib modules
if '' in sys.path:
    sys.path.remove('')

# Prioritize src directory for consolidated modules (including output alias)
src_path = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'src'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Alias forecast_output as output for tests
# import forecast_output
# sys.modules['output'] = forecast_output

# Ensure project root in sys.path for all other packages
project_root = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def main():
    try:
        import pytest
    except ImportError:
        print("pytest is required to run the tests. Please install it via 'pip install pytest'.")
        sys.exit(1)
    test_path = os.path.normpath(os.path.join(os.path.dirname(__file__), "../tests"))
    sys.exit(pytest.main([test_path, "-q", "--disable-warnings", "--maxfail=1"]))

if __name__ == "__main__":
    main()