"""Tools for AI personas to interact with the filesystem and shell.

These are designed to be LangChain-compatible when we add that dependency,
but work standalone for now.
"""

import os
import subprocess
from pathlib import Path
from typing import Callable


# Simple tool registry
TOOLS: dict[str, Callable] = {}


def tool(func: Callable) -> Callable:
    """Register a function as a tool.

    This decorator is a placeholder that mimics LangChain's @tool.
    When we add LangChain, we can swap to their decorator.
    """
    # Store metadata for later use
    func.is_tool = True
    func.tool_name = func.__name__
    func.tool_description = func.__doc__ or ""

    # Register in our tool registry
    TOOLS[func.__name__] = func
    return func


@tool
def read_file(path: str) -> str:
    """Read the contents of a file.

    Args:
        path: Path to the file to read

    Returns:
        The file contents as a string
    """
    try:
        return Path(path).read_text()
    except FileNotFoundError:
        return f"Error: File not found: {path}"
    except Exception as e:
        return f"Error reading file: {e}"


@tool
def write_file(path: str, content: str) -> str:
    """Write content to a file. Creates parent directories if needed.

    Args:
        path: Path to the file to write
        content: Content to write to the file

    Returns:
        Success or error message
    """
    try:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
        return f"Successfully wrote {len(content)} bytes to {path}"
    except Exception as e:
        return f"Error writing file: {e}"


@tool
def list_files(path: str = ".") -> str:
    """List files and directories at the given path.

    Args:
        path: Directory path to list (default: current directory)

    Returns:
        Newline-separated list of files and directories
    """
    try:
        entries = []
        for entry in sorted(Path(path).iterdir()):
            prefix = "📁 " if entry.is_dir() else "📄 "
            entries.append(f"{prefix}{entry.name}")
        return "\n".join(entries) if entries else "(empty directory)"
    except FileNotFoundError:
        return f"Error: Directory not found: {path}"
    except Exception as e:
        return f"Error listing directory: {e}"


@tool
def run_command(command: str) -> str:
    """Run a shell command and return its output.

    Args:
        command: The shell command to run

    Returns:
        Command output (stdout and stderr combined)
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=os.getcwd()
        )
        output = result.stdout + result.stderr
        return output.strip() if output.strip() else "(no output)"
    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 30 seconds"
    except Exception as e:
        return f"Error running command: {e}"


@tool
def search_files(pattern: str, path: str = ".") -> str:
    """Search for files matching a glob pattern.

    Args:
        pattern: Glob pattern (e.g., "*.py", "**/*.json")
        path: Directory to search in (default: current directory)

    Returns:
        Newline-separated list of matching file paths
    """
    try:
        matches = list(Path(path).glob(pattern))
        if matches:
            return "\n".join(str(m) for m in sorted(matches))
        return f"No files matching '{pattern}'"
    except Exception as e:
        return f"Error searching files: {e}"


def get_tool_schema(func: Callable) -> dict:
    """Generate a tool schema for function calling APIs.

    This format works with both Ollama and Claude/OpenAI APIs.
    """
    import inspect

    sig = inspect.signature(func)
    properties = {}
    required = []

    for name, param in sig.parameters.items():
        # Basic type mapping
        type_map = {str: "string", int: "integer", float: "number", bool: "boolean"}
        param_type = "string"  # default

        if param.annotation != inspect.Parameter.empty:
            param_type = type_map.get(param.annotation, "string")

        properties[name] = {"type": param_type}

        if param.default == inspect.Parameter.empty:
            required.append(name)

    return {
        "type": "function",
        "function": {
            "name": func.__name__,
            "description": func.__doc__.split("\n")[0] if func.__doc__ else "",
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required
            }
        }
    }


def list_tools() -> None:
    """Print all registered tools."""
    print("Available tools:")
    for name, func in TOOLS.items():
        desc = func.__doc__.split("\n")[0] if func.__doc__ else "No description"
        print(f"  {name}: {desc}")


if __name__ == "__main__":
    # Quick test
    list_tools()
    print()
    print("Testing tools:")
    print("-" * 40)
    print(f"list_files('.'):\n{list_files('.')}")
    print()
    print(f"run_command('echo hello'):\n{run_command('echo hello')}")
