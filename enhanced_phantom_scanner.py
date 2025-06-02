import os
import ast
import sys
from typing import Dict, List, Tuple, Optional, Set
from collections import defaultdict


class EnhancedPhantomScanner:
    """
    Enhanced scanner to detect and categorize phantom functions in the codebase.
    Tracks imports and provides more context about where functions are called.
    """

    def __init__(self, root_dir: str) -> None:
        self.root_dir: str = root_dir
        self.defined_functions: Set[str] = set()  # Functions defined in the codebase
        self.called_functions: Dict[str, Set[str]] = defaultdict(
            set
        )  # Function -> files where called
        self.imported_names: Dict[str, Set[str]] = defaultdict(
            set
        )  # Module -> imported names
        self.module_imports: Dict[str, Set[str]] = defaultdict(
            set
        )  # File -> imported modules
        self.module_aliases: Dict[str, Dict[str, str]] = defaultdict(
            dict
        )  # File -> {alias: module}
        self.function_contexts: Dict[str, List[Tuple[str, int]]] = defaultdict(
            list
        )  # Function -> (file, line number) contexts

    def scan(self) -> None:
        """Scan the entire codebase to detect phantom functions with context."""
        print(f"Scanning directory: {self.root_dir}")
        for dirpath, dirnames, filenames in os.walk(self.root_dir):
            # Ignore hidden directories and common non-project directories
            dirnames[:] = [
                d
                for d in dirnames
                if not d.startswith(".")
                and d not in {"__pycache__", "venv", ".git", "node_modules"}
            ]

            for filename in filenames:
                if filename.endswith(".py"):
                    file_path: str = os.path.join(dirpath, filename)
                    rel_path: str = os.path.relpath(file_path, self.root_dir)
                    self._process_file(file_path, rel_path)

    def _process_file(self, filepath: str, rel_path: str) -> None:
        """Process a Python file to extract definitions, imports, and calls."""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                file_content: str = f.read()

            tree: ast.Module = ast.parse(file_content, filename=filepath)

            # Find all imports and function definitions first
            for node in ast.walk(tree):
                # Track function definitions
                if isinstance(node, ast.FunctionDef):
                    self.defined_functions.add(node.name)

                # Track imports
                elif isinstance(node, ast.Import):
                    for name in node.names:
                        self.module_imports[rel_path].add(name.name)
                        if name.asname:
                            self.module_aliases[rel_path][name.asname] = name.name

                # Track from-imports
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        module: str = node.module
                        for name in node.names:
                            if name.name == "*":
                                # Can't track * imports statically
                                continue
                            self.imported_names[module].add(name.name)
                            self.module_imports[rel_path].add(module)
                            if name.asname:
                                self.imported_names[module].add(name.asname)

            # Now track function calls and contextual information
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func_name: Optional[str] = self._extract_name(node.func)
                    if func_name:
                        self.called_functions[func_name].add(rel_path)
                        # Add line number context
                        if hasattr(node, "lineno"):
                            context: Tuple[str, int] = (rel_path, node.lineno)
                            self.function_contexts[func_name].append(context)

        except Exception as e:
            print(f"[WARNING] Failed to parse {filepath}: {e}")

    def _extract_name(self, func: ast.expr) -> Optional[str]:
        """Extract function name from a function call node."""
        if isinstance(func, ast.Name):
            return func.id
        elif isinstance(func, ast.Attribute):
            return func.attr  # Returns just the method name
        return None

    def find_true_phantoms(self) -> Dict[str, List[Tuple[str, int]]]:
        """
        Identifies functions that are called but not defined or imported.
        Returns a dictionary of phantom function names -> list of (file, line) contexts.
        """
        # Flatten all imported names
        all_imported: Set[str] = set()
        for names in self.imported_names.values():
            all_imported.update(names)

        # Find functions that are called but neither defined nor imported
        phantom_functions: Dict[str, List[Tuple[str, int]]] = {}
        for func_name, files in self.called_functions.items():
            if (
                func_name not in self.defined_functions
                and func_name not in all_imported
            ):
                # This appears to be a true phantom function
                phantom_functions[func_name] = self.function_contexts[func_name]

        return phantom_functions

    def categorize_phantom_functions(self) -> Dict[str, List[str]]:
        """
        Categorize phantom functions into likely categories:
        - Standard library functions
        - Third-party library functions
        - Internal missing functions
        """
        # Common standard library and third-party modules
        # This is a simplification - in a real implementation you'd want to
        # check against actual modules in sys.modules or a more comprehensive list
        std_lib_prefixes: Set[str] = {
            "os_",
            "sys_",
            "math_",
            "json_",
            "re_",
            "random_",
            "datetime_",
            "time_",
            "file_",
            "path_",
            "str_",
            "list_",
            "dict_",
            "set_",
            "get_",
        }

        ml_lib_prefixes: Set[str] = {
            "np_",
            "pd_",
            "plt_",
            "torch_",
            "tf_",
            "keras_",
            "sklearn_",
            "model_",
            "layer_",
            "optimizer_",
            "loss_",
            "activation_",
        }

        # Project-specific prefixes (customize based on your project)
        project_prefixes: Set[str] = {
            "pulse_",
            "forecast_",
            "sim_",
            "causal_",
            "world_",
            "trust_",
            "symbolic_",
            "capital_",
            "rule_",
            "state_",
            "memory_",
        }

        categories: Dict[str, List[str]] = {
            "standard_lib": [],
            "ml_libraries": [],
            "project_specific": [],
            "unknown": [],
        }

        true_phantoms: Dict[str, List[Tuple[str, int]]] = self.find_true_phantoms()

        for func_name in true_phantoms:
            # Check each function name against our prefix sets
            categorized: bool = False

            for prefix in std_lib_prefixes:
                if func_name.startswith(prefix) or func_name.lower().startswith(prefix):
                    categories["standard_lib"].append(func_name)
                    categorized = True
                    break

            if not categorized:
                for prefix in ml_lib_prefixes:
                    if func_name.startswith(prefix) or func_name.lower().startswith(
                        prefix
                    ):
                        categories["ml_libraries"].append(func_name)
                        categorized = True
                        break

            if not categorized:
                for prefix in project_prefixes:
                    if func_name.startswith(prefix) or func_name.lower().startswith(
                        prefix
                    ):
                        categories["project_specific"].append(func_name)
                        categorized = True
                        break

            if not categorized:
                categories["unknown"].append(func_name)

        return categories

    def report(self, max_contexts: int = 3) -> None:
        """
        Generate a comprehensive report of phantom functions.
        Args:
            max_contexts: Maximum number of call contexts to show per function
        """
        true_phantoms: Dict[str, List[Tuple[str, int]]] = self.find_true_phantoms()
        categories: Dict[str, List[str]] = self.categorize_phantom_functions()

        print("\n=== Enhanced Phantom Function Report ===")
        print(f"Total Functions Defined: {len(self.defined_functions)}")
        print(f"Total Functions Called: {len(self.called_functions)}")
        print(f"Total Phantom Functions: {len(true_phantoms)}")

        # Print categorized summary
        print("\n=== Phantom Function Categories ===")
        for category, funcs in categories.items():
            print(f"{category}: {len(funcs)} functions")

        # Print detailed report for project-specific phantom functions (highest priority)
        print("\n=== Project-Specific Phantom Functions (Highest Priority) ===")
        for func in sorted(categories["project_specific"]):
            contexts: List[Tuple[str, int]] = true_phantoms[func][:max_contexts]
            context_strs: List[str] = [f"{file}:{line}" for file, line in contexts]
            more: str = (
                ""
                if len(contexts) <= max_contexts
                else f" (and {len(true_phantoms[func]) - max_contexts} more...)"
            )

            print(f" - {func}(): Called in {', '.join(context_strs)}{more}")

        # Print a summary of unknown functions
        print(f"\n=== Unknown Phantom Functions ({len(categories['unknown'])}) ===")
        if len(categories["unknown"]) > 0:
            for func in sorted(categories["unknown"])[:20]:  # Show top 20
                contexts = true_phantoms[func][:2]
                context_strs = [f"{file}:{line}" for file, line in contexts]
                print(f" - {func}(): Called in {', '.join(context_strs)}")

            if len(categories["unknown"]) > 20:
                print(f"   ... and {len(categories['unknown']) - 20} more")

        # Print recommended actions
        print("\n=== Recommended Actions ===")
        print("1. Implement missing project-specific functions")
        print("2. Add proper imports for standard library functions")
        print("3. Install and import required third-party libraries")
        print("4. Review 'unknown' category functions for false positives")


def main() -> None:
    if len(sys.argv) > 1:
        project_path: str = sys.argv[1]
    else:
        project_path = input("Enter path to Pulse project root: ").strip().strip('"')

    scanner: EnhancedPhantomScanner = EnhancedPhantomScanner(project_path)
    print("Scanning for phantom functions with enhanced context...")
    scanner.scan()
    scanner.report()


if __name__ == "__main__":
    main()
