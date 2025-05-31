import os
import ast
from typing import Set, Optional, Any


class FullPhantomScanner:
    def __init__(self, root_dir: str) -> None:
        self.root_dir: str = root_dir
        self.defined_functions: Set[str] = set()
        self.called_functions: Set[str] = set()

    def scan(self) -> None:
        for dirpath, dirnames, filenames in os.walk(self.root_dir):
            # Ignore hidden directories
            dirnames[:] = [d for d in dirnames if not d.startswith(".")]
            for filename in filenames:
                if filename.endswith(".py"):
                    self._process_file(os.path.join(dirpath, filename))
        self._report()

    def _process_file(self, filepath: str) -> None:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=filepath)
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        self.defined_functions.add(node.name)
                    elif isinstance(node, ast.Call):
                        func_name: Optional[str] = self._extract_name(node.func)
                        if func_name:
                            self.called_functions.add(func_name)
        except Exception as e:
            print(f"[WARNING] Failed to parse {filepath}: {e}")

    def _extract_name(self, func: ast.expr) -> Optional[str]:
        if isinstance(func, ast.Name):
            return func.id
        elif isinstance(func, ast.Attribute):
            return func.attr
        return None

    def _report(self) -> None:
        missing: Set[str] = self.called_functions - self.defined_functions
        print("\n=== Full Scan Report ===")
        print(f"Total Functions Defined: {len(self.defined_functions)}")
        print(f"Total Functions Called: {len(self.called_functions)}")
        if missing:
            print("\n❌ Potential Phantoms (no local definition or import seen):")
            for name in sorted(list(missing)): # Ensure sorted takes an iterable like list
                print(f" - {name}()")
        else:
            print("\n✅ No phantom calls detected (locally).")


if __name__ == "__main__":
    project_path: str = input("Enter path to Pulse project root: ").strip().strip('"')
    scanner: FullPhantomScanner = FullPhantomScanner(project_path)
    scanner.scan()
