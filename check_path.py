import sys
import os

print("Current working directory:", os.getcwd())
print("sys.path:")
for p in sys.path:
    print(f"- {p}")

