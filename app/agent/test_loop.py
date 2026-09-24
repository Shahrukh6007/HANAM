"""Runs the project's tests. If they fail, asks the LLM to fix them."""

import re
import subprocess
from pathlib import Path

from app.llm.cloud_router import ask_hanam_bulletproof


PROJECT_ROOT = Path(__file__).resolve().parents[2]
MAX_ATTEMPTS = 3
TIMEOUT = 180


FIX_SYSTEM_PROMPT = (
    "You are a coding assistant fixing a failing test. "
    "You will be given the test output, the contents of the test file, "
    "and the list of files in the workspace. "
    "Fix the SOURCE file so the test passes. Do NOT edit the test file. "
    "Use read_file to see the source, then edit_file with old_text and "
    "new_text to fix it. Be concise."
)


def _detect_test_command():
    if (PROJECT_ROOT / "tests").is_dir():
        return "python -m pytest tests/ -x --tb=short -q"
    return None


def _run_tests(cmd):
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=TIMEOUT,
            encoding="utf-8",
            errors="replace",
        )
    except subprocess.TimeoutExpired:
        return False, f"Tests timed out after {TIMEOUT}s."
    except Exception as error:
        return False, f"Failed to run tests: {error}"

    output = result.stdout
    if result.stderr:
        output += "\n" + result.stderr

    return result.returncode == 0, output.strip()


def _extract_test_files(output):
    """Find test file paths mentioned in pytest output."""
    paths = set()
    for m in re.finditer(r"(tests[\\/][\w\\/.]+\.py)", output):
        paths.add(m.group(1).replace("\\", "/"))
    return paths


def _read_test_files(output):
    """Read the content of test files mentioned in pytest output."""
    paths = _extract_test_files(output)
    chunks = []
    for rel in paths:
        full = PROJECT_ROOT / rel
        if full.exists():
            try:
                content = full.read_text(encoding="utf-8")
                chunks.append(f"### {rel}\n```python\n{content}\n```")
            except Exception:
                pass
    return "\n\n".join(chunks) if chunks else "(test file content unavailable)"


def _list_workspace_files():
    workspace = PROJECT_ROOT / "workspace"
    if not workspace.exists():
        return "(no workspace)"
    files = sorted(f.name for f in workspace.iterdir() if f.is_file())
    return ", ".join(files) if files else "(empty)"


def test_and_fix():
    cmd = _detect_test_command()
    if cmd is None:
        return "No tests/ folder found. Create one first."

    print(f"\n[HANAM will run] {cmd}")
    try:
        answer = input("Run tests and auto-fix failures? [y/N] ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        return "Cancelled."

    if answer not in ("y", "yes"):
        return "Cancelled."

    for attempt in range(1, MAX_ATTEMPTS + 1):
        print(f"\n[HANAM] Attempt {attempt}/{MAX_ATTEMPTS}: running tests...")
        passed, output = _run_tests(cmd)

        if passed:
            return f"Tests pass on attempt {attempt}/{MAX_ATTEMPTS}.\n{output[:500]}"

        print("[HANAM] Tests failed. Asking LLM to fix...")

        fix_prompt = (
            "The project's tests are failing.\n\n"
            f"## Test output\n```\n{output[:3000]}\n```\n\n"
            f"## Test file contents\n{_read_test_files(output)}\n\n"
            f"## Files in the workspace\n{_list_workspace_files()}\n\n"
            "Fix the SOURCE file so the test passes. Do NOT edit the test. "
            "Read the source first, then edit it with edit_file "
            "(old_text, new_text)."
        )

        messages = [
            {"role": "system", "content": FIX_SYSTEM_PROMPT},
            {"role": "user", "content": fix_prompt},
        ]

        try:
            summary = ask_hanam_bulletproof(fix_prompt, messages=messages)
            print(f"[HANAM] Fix summary: {(summary or '')[:200]}")
        except Exception as error:
            return f"LLM error while fixing: {error}"

    passed, output = _run_tests(cmd)
    if passed:
        return f"Tests pass after {MAX_ATTEMPTS} attempts."
    return f"Still failing after {MAX_ATTEMPTS} attempts.\n{output[:2000]}"