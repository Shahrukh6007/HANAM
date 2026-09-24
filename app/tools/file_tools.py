from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[2] / "workspace"
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def get_file_path(filename: str) -> Path:
    """Return a safe path inside the HANAM workspace."""
    file_path = (WORKSPACE / filename).resolve()

    if not file_path.is_relative_to(WORKSPACE.resolve()):
        raise ValueError("File path must stay inside the HANAM workspace.")

    return file_path


def read_file(filename: str) -> str:
    """Read a text file from the HANAM workspace."""
    try:
        file_path = get_file_path(filename)
    except ValueError as error:
        return str(error)

    if not file_path.exists():
        return f"File '{filename}' was not found."

    if not file_path.is_file():
        return f"'{filename}' is not a file."

    try:
        return file_path.read_text(encoding="utf-8")
    except Exception as error:
        return f"Failed to read '{filename}': {error}"


def list_files() -> str:
    """List all files in the HANAM workspace."""
    if not WORKSPACE.exists():
        return "The workspace is empty."

    skip = {".git", "venv", ".venv", "__pycache__", "node_modules"}

    files = []
    for f in WORKSPACE.rglob("*"):
        if not f.is_file():
            continue
        if any(part in skip for part in f.parts):
            continue
        if f.suffix in {".pyc", ".pyo"}:
            continue
        files.append(str(f.relative_to(WORKSPACE)))

    if not files:
        return "The workspace is empty."

    return "Files in the workspace:\n" + "\n".join(f"- {f}" for f in files)


def create_file(filename: str, content: str) -> str:
    """Create a new text file in the HANAM workspace."""
    try:
        file_path = get_file_path(filename)
    except ValueError as error:
        return str(error)

    if file_path.exists():
        return f"File '{filename}' already exists."

    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        return f"File '{filename}' created successfully."
    except Exception as error:
        return f"Failed to create '{filename}': {error}"


def edit_file(filename: str, old_text: str, new_text: str = "") -> str:
    """Surgically replace old_text with new_text in an existing file.

    Safety rules:
      - File must exist.
      - old_text must appear exactly once. Zero or multiple matches = refuse.
      - new_text defaults to "" (delete the matched text).
    """
    try:
        file_path = get_file_path(filename)
    except ValueError as error:
        return str(error)

    if not file_path.exists():
        return f"File '{filename}' was not found."

    if not file_path.is_file():
        return f"'{filename}' is not a file."

    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as error:
        return f"Failed to read '{filename}': {error}"

    count = content.count(old_text)
    if count == 0:
        return (
            f"Text not found in '{filename}'. "
            f"Read the file first to see its current contents."
        )
    if count > 1:
        return (
            f"Text appears {count} times in '{filename}'. "
            f"Provide more surrounding context so it's unique."
        )

    new_content = content.replace(old_text, new_text, 1)

    try:
        file_path.write_text(new_content, encoding="utf-8")
        return f"File '{filename}' edited successfully."
    except Exception as error:
        return f"Failed to edit '{filename}': {error}"


def write_file(filename: str, content: str) -> str:
    """Create a new file OR completely overwrite an existing one.

    Use only when the user explicitly asks to rewrite a file.
    For surgical edits, use edit_file instead.
    """
    try:
        file_path = get_file_path(filename)
    except ValueError as error:
        return str(error)

    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        return f"File '{filename}' written successfully."
    except Exception as error:
        return f"Failed to write '{filename}': {error}"


def grep(pattern: str, path: str = ".") -> str:
    """Search for a pattern in all text files in the workspace.

    Returns matching lines with file:line_number prefix.
    """
    import re

    try:
        base = get_file_path(path) if path != "." else WORKSPACE
    except ValueError as error:
        return str(error)

    if not base.exists():
        return f"Path '{path}' not found."

    try:
        regex = re.compile(pattern)
    except re.error:
        regex = re.compile(re.escape(pattern))

    matches = []
    files_scanned = 0
    MAX_MATCHES = 100

    for file in base.rglob("*"):
        if not file.is_file():
            continue
        if any(
            part in {".git", "node_modules", "venv", ".venv", "__pycache__"}
            for part in file.parts
        ):
            continue

        try:
            text = file.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue

        files_scanned += 1

        for lineno, line in enumerate(text.splitlines(), start=1):
            if regex.search(line):
                rel = file.relative_to(WORKSPACE)
                matches.append(f"{rel}:{lineno}: {line.strip()}")
                if len(matches) >= MAX_MATCHES:
                    break

        if len(matches) >= MAX_MATCHES:
            break

    if not matches:
        return f"No matches for '{pattern}' (scanned {files_scanned} files)."

    header = f"Found {len(matches)} match(es) for '{pattern}':\n"
    return header + "\n".join(matches)


def grep_project(pattern: str) -> str:
    """Search the whole HANAM project (not just the workspace)."""
    import re

    try:
        regex = re.compile(pattern)
    except re.error:
        regex = re.compile(re.escape(pattern))

    SKIP = {
        ".git",
        "node_modules",
        "venv",
        ".venv",
        "__pycache__",
        ".pytest_cache",
        "workspace",
        "sessions",
        "dist",
        "build",
        "app_v4_backup",
        "_backup",
    }

    matches = []
    files_scanned = 0
    MAX_MATCHES = 100

    for file in PROJECT_ROOT.rglob("*"):
        if not file.is_file():
            continue
        if any(part in SKIP for part in file.parts):
            continue
        if "_backup" in file.name or file.name.endswith("_backup.py"):
            continue
        if file.suffix == ".pyc":
            continue

        try:
            text = file.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue

        files_scanned += 1

        for lineno, line in enumerate(text.splitlines(), start=1):
            if regex.search(line):
                rel = file.relative_to(PROJECT_ROOT)
                matches.append(f"{rel}:{lineno}: {line.strip()}")
                if len(matches) >= MAX_MATCHES:
                    break

        if len(matches) >= MAX_MATCHES:
            break

    if not matches:
        return f"No matches for '{pattern}' (scanned {files_scanned} files)."

    header = f"Found {len(matches)} match(es) for '{pattern}':\n"
    return header + "\n".join(matches)
