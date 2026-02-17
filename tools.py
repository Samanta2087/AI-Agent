"""
Autonomous Coding Agent — Tool Implementations
All file operations, shell execution, git, and search tools.
"""
import os
import re
import subprocess
import shutil
import difflib
import fnmatch
from pathlib import Path
from typing import Optional
from config import WORKSPACE_DIR, COMMAND_TIMEOUT, BLOCKED_COMMANDS, ALLOWED_EXTENSIONS


class ToolError(Exception):
    """Raised when a tool execution fails."""
    pass


def _resolve_path(rel_path: str) -> str:
    """Resolve a relative path to absolute within the workspace. Prevent path traversal."""
    workspace = os.path.abspath(WORKSPACE_DIR)
    full = os.path.normpath(os.path.join(workspace, rel_path))
    if not full.startswith(workspace):
        raise ToolError(f"Path traversal blocked: {rel_path}")
    return full


def _ensure_workspace():
    """Ensure workspace directory exists."""
    os.makedirs(WORKSPACE_DIR, exist_ok=True)


# ─────────────────────────────────────────────────────────────────
# TOOL: create_file
# ─────────────────────────────────────────────────────────────────
def create_file(path: str, content: str) -> dict:
    """Create a new file with the given content."""
    _ensure_workspace()
    full_path = _resolve_path(path)

    # Create parent directories
    os.makedirs(os.path.dirname(full_path), exist_ok=True)

    if os.path.exists(full_path):
        return {
            "success": False,
            "output": f"File already exists: {path}. Use edit_file to modify it.",
        }

    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

    return {
        "success": True,
        "output": f"Created: {path} ({len(content)} bytes, {content.count(chr(10))+1} lines)",
    }


# ─────────────────────────────────────────────────────────────────
# TOOL: edit_file (unified diff)
# ─────────────────────────────────────────────────────────────────
def edit_file(path: str, diff_text: str) -> dict:
    """Apply a unified diff patch to an existing file."""
    full_path = _resolve_path(path)

    if not os.path.exists(full_path):
        return {"success": False, "output": f"File not found: {path}"}

    with open(full_path, "r", encoding="utf-8") as f:
        original_lines = f.readlines()

    try:
        patched_lines = _apply_unified_diff(original_lines, diff_text)
    except Exception as e:
        return {"success": False, "output": f"Failed to apply diff: {e}"}

    with open(full_path, "w", encoding="utf-8") as f:
        f.writelines(patched_lines)

    changes = len([1 for a, b in zip(original_lines, patched_lines) if a != b])
    return {
        "success": True,
        "output": f"Patched: {path} ({changes} lines changed)",
    }


def _apply_unified_diff(original_lines: list[str], diff_text: str) -> list[str]:
    """
    Apply a unified diff to original file lines.
    Handles @@ hunk headers and +/- line markers.
    Falls back to fuzzy matching if exact match fails.
    """
    result = list(original_lines)

    # Parse hunks from the diff
    hunks = _parse_diff_hunks(diff_text)

    if not hunks:
        raise ToolError("No valid hunks found in diff")

    # Apply hunks in reverse order (so line numbers stay valid)
    offset = 0
    for hunk in hunks:
        old_start = hunk["old_start"] - 1  # Convert to 0-indexed
        old_lines = hunk["old_lines"]
        new_lines = hunk["new_lines"]

        # Try exact match first
        matched_pos = _find_hunk_position(result, old_lines, old_start + offset)

        if matched_pos is None:
            raise ToolError(
                f"Could not find matching lines at position {old_start + 1}. "
                f"Expected:\n" + "".join(old_lines[:5])
            )

        # Replace the old lines with new lines
        result[matched_pos : matched_pos + len(old_lines)] = new_lines
        offset += len(new_lines) - len(old_lines)

    return result


def _parse_diff_hunks(diff_text: str) -> list[dict]:
    """Parse unified diff text into hunk objects."""
    hunks = []
    lines = diff_text.strip().split("\n")
    i = 0

    while i < len(lines):
        line = lines[i]

        # Skip --- and +++ header lines
        if line.startswith("---") or line.startswith("+++"):
            i += 1
            continue

        # Parse @@ header
        hunk_match = re.match(r"@@ -(\d+)(?:,\d+)? \+\d+(?:,\d+)? @@", line)
        if hunk_match:
            old_start = int(hunk_match.group(1))
            old_lines = []
            new_lines = []
            i += 1

            while i < len(lines):
                l = lines[i]
                if l.startswith("@@") or l.startswith("---") or l.startswith("+++"):
                    break
                if l.startswith("-"):
                    old_lines.append(l[1:] + "\n")
                elif l.startswith("+"):
                    new_lines.append(l[1:] + "\n")
                elif l.startswith(" ") or l == "":
                    content = (l[1:] if l.startswith(" ") else l) + "\n"
                    old_lines.append(content)
                    new_lines.append(content)
                else:
                    # Treat as context line
                    old_lines.append(l + "\n")
                    new_lines.append(l + "\n")
                i += 1

            hunks.append({
                "old_start": old_start,
                "old_lines": old_lines,
                "new_lines": new_lines,
            })
        else:
            i += 1

    # If no @@ headers found, try simple +/- parsing
    if not hunks:
        hunks = _parse_simple_diff(diff_text)

    return hunks


def _parse_simple_diff(diff_text: str) -> list[dict]:
    """Parse simple diff format without @@ headers."""
    lines = diff_text.strip().split("\n")
    old_lines = []
    new_lines = []

    for line in lines:
        if line.startswith("---") or line.startswith("+++"):
            continue
        elif line.startswith("-"):
            old_lines.append(line[1:] + "\n")
        elif line.startswith("+"):
            new_lines.append(line[1:] + "\n")
        elif line.startswith(" "):
            old_lines.append(line[1:] + "\n")
            new_lines.append(line[1:] + "\n")

    if old_lines or new_lines:
        return [{"old_start": 1, "old_lines": old_lines, "new_lines": new_lines}]
    return []


def _find_hunk_position(file_lines: list[str], old_lines: list[str], hint_pos: int) -> Optional[int]:
    """Find where old_lines exist in file_lines, starting from hint position."""
    if not old_lines:
        # Pure addition — insert at hint position
        return hint_pos

    # Normalize for comparison
    def norm(s):
        return s.rstrip("\n").rstrip()

    target = [norm(l) for l in old_lines]

    # Try exact position first
    if hint_pos >= 0 and hint_pos + len(old_lines) <= len(file_lines):
        chunk = [norm(file_lines[hint_pos + j]) for j in range(len(old_lines))]
        if chunk == target:
            return hint_pos

    # Search nearby (within 50 lines)
    for delta in range(1, 50):
        for pos in [hint_pos - delta, hint_pos + delta]:
            if pos >= 0 and pos + len(old_lines) <= len(file_lines):
                chunk = [norm(file_lines[pos + j]) for j in range(len(old_lines))]
                if chunk == target:
                    return pos

    # Search entire file
    for pos in range(len(file_lines) - len(old_lines) + 1):
        chunk = [norm(file_lines[pos + j]) for j in range(len(old_lines))]
        if chunk == target:
            return pos

    return None


# ─────────────────────────────────────────────────────────────────
# TOOL: read_file
# ─────────────────────────────────────────────────────────────────
def read_file(path: str, start_line: int = None, end_line: int = None) -> dict:
    """Read file contents, optionally a specific line range."""
    full_path = _resolve_path(path)

    if not os.path.exists(full_path):
        return {"success": False, "output": f"File not found: {path}"}

    try:
        with open(full_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        return {"success": False, "output": f"Cannot read binary file: {path}"}

    total = len(lines)

    if start_line and end_line:
        start = max(0, start_line - 1)
        end = min(total, end_line)
        content = "".join(lines[start:end])
        header = f"File: {path} (lines {start_line}-{end_line} of {total})\n"
    else:
        # Limit to first 500 lines for large files
        if total > 500:
            content = "".join(lines[:500])
            header = f"File: {path} ({total} lines, showing first 500)\n"
        else:
            content = "".join(lines)
            header = f"File: {path} ({total} lines)\n"

    return {"success": True, "output": header + content}


# ─────────────────────────────────────────────────────────────────
# TOOL: list_dir
# ─────────────────────────────────────────────────────────────────
def list_dir(path: str = ".") -> dict:
    """List directory contents with file sizes."""
    full_path = _resolve_path(path)

    if not os.path.isdir(full_path):
        return {"success": False, "output": f"Not a directory: {path}"}

    items = []
    try:
        for entry in sorted(os.listdir(full_path)):
            entry_path = os.path.join(full_path, entry)
            if os.path.isdir(entry_path):
                count = sum(1 for _ in Path(entry_path).rglob("*") if _.is_file())
                items.append(f"  📁 {entry}/ ({count} files)")
            else:
                size = os.path.getsize(entry_path)
                if size < 1024:
                    sz = f"{size}B"
                elif size < 1024 * 1024:
                    sz = f"{size/1024:.1f}KB"
                else:
                    sz = f"{size/(1024*1024):.1f}MB"
                items.append(f"  📄 {entry} ({sz})")
    except PermissionError:
        return {"success": False, "output": f"Permission denied: {path}"}

    output = f"Directory: {path}/\n" + "\n".join(items) if items else f"Directory: {path}/ (empty)"
    return {"success": True, "output": output}


# ─────────────────────────────────────────────────────────────────
# TOOL: run_command
# ─────────────────────────────────────────────────────────────────
def run_command(command: str, timeout: int = None) -> dict:
    """Execute a shell command inside the workspace."""
    _ensure_workspace()

    if timeout is None:
        timeout = COMMAND_TIMEOUT

    # Safety check
    for blocked in BLOCKED_COMMANDS:
        if blocked in command:
            return {"success": False, "output": f"BLOCKED: dangerous command detected: {blocked}"}

    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=WORKSPACE_DIR,
            capture_output=True,
            text=True,
            timeout=timeout,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )

        output_parts = []
        if result.stdout:
            output_parts.append(result.stdout)
        if result.stderr:
            output_parts.append(f"[STDERR]\n{result.stderr}")

        output = "\n".join(output_parts) or "(no output)"

        # Truncate if too long (keep first and last parts)
        if len(output) > 8000:
            output = output[:4000] + "\n\n... (truncated) ...\n\n" + output[-4000:]

        return {
            "success": result.returncode == 0,
            "output": f"$ {command}\nExit code: {result.returncode}\n{output}",
        }

    except subprocess.TimeoutExpired:
        return {"success": False, "output": f"Command timed out after {timeout}s: {command}"}
    except Exception as e:
        return {"success": False, "output": f"Command failed: {e}"}


# ─────────────────────────────────────────────────────────────────
# TOOL: search_files
# ─────────────────────────────────────────────────────────────────
def search_files(pattern: str, path: str = ".", glob_pattern: str = None) -> dict:
    """Search for text pattern in files using grep-like behavior."""
    full_path = _resolve_path(path)

    if not os.path.exists(full_path):
        return {"success": False, "output": f"Path not found: {path}"}

    matches = []
    max_matches = 50

    def should_search(filepath: str) -> bool:
        if glob_pattern and not fnmatch.fnmatch(os.path.basename(filepath), glob_pattern):
            return False
        ext = os.path.splitext(filepath)[1].lower()
        if ext and ext not in ALLOWED_EXTENSIONS:
            return False
        return True

    for root, dirs, files in os.walk(full_path):
        # Skip hidden dirs and common non-code dirs
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in {
            "node_modules", "__pycache__", "venv", ".venv", "dist", "build", ".git"
        }]

        for fname in files:
            if len(matches) >= max_matches:
                break
            fpath = os.path.join(root, fname)
            if not should_search(fpath):
                continue
            try:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    for line_num, line in enumerate(f, 1):
                        if pattern in line:
                            rel = os.path.relpath(fpath, full_path)
                            matches.append(f"  {rel}:{line_num}: {line.rstrip()}")
                            if len(matches) >= max_matches:
                                break
            except (OSError, PermissionError):
                continue

    if matches:
        output = f"Found {len(matches)} matches for '{pattern}':\n" + "\n".join(matches)
    else:
        output = f"No matches found for '{pattern}' in {path}/"

    return {"success": True, "output": output}


# ─────────────────────────────────────────────────────────────────
# TOOL: git
# ─────────────────────────────────────────────────────────────────
def git_command(args: str) -> dict:
    """Run a git command in the workspace."""
    _ensure_workspace()

    # Initialize git if needed
    git_dir = os.path.join(WORKSPACE_DIR, ".git")
    if not os.path.isdir(git_dir):
        subprocess.run(
            ["git", "init"],
            cwd=WORKSPACE_DIR,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.email", "agent@localhost"],
            cwd=WORKSPACE_DIR,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Coding Agent"],
            cwd=WORKSPACE_DIR,
            capture_output=True,
        )

    return run_command(f"git {args}")


# ─────────────────────────────────────────────────────────────────
# TOOL: delete_file
# ─────────────────────────────────────────────────────────────────
def delete_file(path: str) -> dict:
    """Delete a file from the workspace."""
    full_path = _resolve_path(path)

    if not os.path.exists(full_path):
        return {"success": False, "output": f"File not found: {path}"}

    if os.path.isdir(full_path):
        return {"success": False, "output": f"Cannot delete directory with this tool: {path}"}

    os.remove(full_path)
    return {"success": True, "output": f"Deleted: {path}"}


# ─────────────────────────────────────────────────────────────────
# TOOL DISPATCHER
# ─────────────────────────────────────────────────────────────────
TOOL_REGISTRY = {
    "create_file": lambda params: create_file(params["path"], params["content"]),
    "edit_file": lambda params: edit_file(params["path"], params["diff"]),
    "read_file": lambda params: read_file(
        params["path"],
        params.get("start_line"),
        params.get("end_line"),
    ),
    "list_dir": lambda params: list_dir(params.get("path", ".")),
    "run_command": lambda params: run_command(
        params["command"],
        int(params.get("timeout", COMMAND_TIMEOUT)),
    ),
    "search_files": lambda params: search_files(
        params["pattern"],
        params.get("path", "."),
        params.get("glob"),
    ),
    "git": lambda params: git_command(params["command"]),
    "delete_file": lambda params: delete_file(params["path"]),
}


def execute_tool(tool_name: str, params: dict) -> dict:
    """Execute a tool by name with given parameters."""
    if tool_name not in TOOL_REGISTRY and tool_name not in ("done", "ask_user", "review"):
        return {"success": False, "output": f"Unknown tool: {tool_name}"}

    if tool_name in ("done", "ask_user", "review"):
        # These are handled by the agent loop, not here
        return {"success": True, "output": params.get("summary", params.get("question", ""))}

    try:
        return TOOL_REGISTRY[tool_name](params)
    except ToolError as e:
        return {"success": False, "output": f"Tool error: {e}"}
    except KeyError as e:
        return {"success": False, "output": f"Missing required parameter: {e}"}
    except Exception as e:
        return {"success": False, "output": f"Unexpected error: {type(e).__name__}: {e}"}
