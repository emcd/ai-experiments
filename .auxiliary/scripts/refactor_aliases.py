import os
import sys

# Define the mapping of old aliases to new, fully-qualified names
REFACTOR_MAP = {
    "__.abc.ABCMeta": "__.abc.ABCMeta",
    "__.abc.abstractmethod": "__.abc.abstractmethod",
    "__.ctxl.ExitStack": "__.ctxl.ExitStack",
    "__.ctxl.ExitStackAsync": "__.ctxl.AsyncExitStack",
    "__.ctxl.contextmanager": "__.ctxl.contextmanager",
    "__.ctxl.contextmanager_async": "__.ctxl.asynccontextmanager",
    "__.dcls.field": "__.dcls.field",
    "__.enum.auto": "__.enum.auto",
    "__.funct.partial": "__.funct.partial",
    "__.types.MappingProxyType": "__.types.MappingProxyType",
    "__.types.ModuleType": "__.types.ModuleType",
    "__.types.SimpleNamespace": "__.types.SimpleNamespace",
}

def refactor_file(filepath):
    """
    Reads a file and replaces all occurrences of the old aliases with the new,
    fully-qualified names.
    """
    try:
        with open(filepath, "r") as f:
            content = f.read()
    except (IOError, OSError) as e:
        print(f"Error reading file {filepath}: {e}", file=sys.stderr)
        return

    original_content = content
    for old_alias, new_name in REFACTOR_MAP.items():
        content = content.replace(old_alias, new_name)

    if content != original_content:
        try:
            with open(filepath, "w") as f:
                f.write(content)
        except (IOError, OSError) as e:
            print(f"Error writing to file {filepath}: {e}", file=sys.stderr)
            return

def main():
    """
    Walks through the codebase and refactors all Python files.
    """
    for root, _, files in os.walk("."):
        for filename in files:
            if filename.endswith(".py"):
                filepath = os.path.join(root, filename)
                refactor_file(filepath)

if __name__ == "__main__":
    main()
