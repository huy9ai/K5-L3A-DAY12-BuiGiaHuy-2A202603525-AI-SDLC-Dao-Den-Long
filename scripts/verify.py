"""Single-command verification gate and real proof generator."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import re
import subprocess
import sys

ROOT_DIR = Path(__file__).resolve().parent.parent

SECRET_PATTERNS = (
    ("OpenAI/API token", re.compile(r"sk-[A-Za-z0-9]{20,}")),
    ("GitHub token", re.compile(r"ghp_[A-Za-z0-9]{20,}")),
    ("Google API key", re.compile(r"AIza[0-9A-Za-z_-]{20,}")),
    ("AWS access key", re.compile(r"AKIA[0-9A-Z]{16}")),
)

IGNORED_DIRS = {".git", "__pycache__", ".pytest_cache", ".venv", "venv", "node_modules"}


def _git_head_short() -> str:
    proc = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=ROOT_DIR,
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.stdout.strip() if proc.returncode == 0 else "uncommitted"


def _run_unit_tests() -> tuple[bool, str]:
    proc = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
        cwd=ROOT_DIR,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    output = (proc.stdout + proc.stderr).strip()
    return proc.returncode == 0, output


def _run_headless_determinism() -> tuple[bool, str]:
    cmd = [sys.executable, "run.py", "headless", "--seed", "42", "--ticks", "30"]
    run1 = subprocess.run(cmd, cwd=ROOT_DIR, capture_output=True, check=False)
    run2 = subprocess.run(cmd, cwd=ROOT_DIR, capture_output=True, check=False)

    if run1.returncode != 0 or run2.returncode != 0:
        err = (run1.stderr + run2.stderr).decode("utf-8", errors="replace")
        return False, f"Headless execution failed (codes {run1.returncode}, {run2.returncode}):\n{err}"

    hash1 = hashlib.sha256(run1.stdout).hexdigest()
    hash2 = hashlib.sha256(run2.stdout).hexdigest()

    try:
        parsed = json.loads(run1.stdout.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return False, f"Invalid UTF-8/JSON from headless stdout: {exc}"

    same = run1.stdout == run2.stdout and hash1 == hash2
    summary = (
        f"Command: {' '.join(cmd)}\n"
        f"Run 1 SHA-256: {hash1}\n"
        f"Run 2 SHA-256: {hash2}\n"
        f"Byte-identical: {same}\n"
        f"Sample snapshot keys: {sorted(parsed.keys())}, tick={parsed.get('tick')}"
    )
    return same, summary


def _collect_repo_files() -> list[Path]:
    tracked = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT_DIR,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    files: set[Path] = set()
    if tracked.returncode == 0:
        for rel in tracked.stdout.splitlines():
            p = ROOT_DIR / rel
            if p.is_file():
                files.add(p)

    for path in ROOT_DIR.rglob("*"):
        if any(part in IGNORED_DIRS for part in path.parts):
            continue
        if path.is_file():
            files.add(path)
    return sorted(files)


def _run_secret_scan() -> tuple[bool, str]:
    issues: list[str] = []
    scanned = 0
    for file_path in _collect_repo_files():
        rel = file_path.relative_to(ROOT_DIR).as_posix()
        name = file_path.name
        if name == ".env" or (name.startswith(".env.") and name != ".env.example"):
            issues.append(f"Forbidden env file present: {rel}")
            continue

        if file_path.suffix.lower() in {".png", ".jpg", ".mp4", ".pyc", ".ico", ".zip"}:
            continue

        scanned += 1
        try:
            content = file_path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue

        for label, pattern in SECRET_PATTERNS:
            if pattern.search(content):
                issues.append(f"Potential {label} detected in {rel}")

    if issues:
        return False, "\n".join(issues)
    return True, f"Scanned {scanned} text files; 0 env files or secret key patterns found."


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify Dao Den Long build, tests, determinism, and hygiene.")
    parser.add_argument("--quick", action="store_true", help="Run fast gate checks (for pre-commit/hooks)")
    parser.add_argument("--ci", action="store_true", help="Run CI verification with environment metadata")
    parser.add_argument("--phase", default="cp0", help="Phase name for proof directory (default: cp0)")
    parser.add_argument("--write-proof", action="store_true", help="Write raw output to docs/proof/<phase>/verify-output.txt")
    args = parser.parse_args(argv)

    mode = "quick" if args.quick else ("ci" if args.ci else "standard")
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    git_rev = _git_head_short()

    checks = [
        ("Unit & Smoke Tests (unittest)", _run_unit_tests),
        ("Headless Determinism (SHA-256 x2)", _run_headless_determinism),
        ("Secret & Hygiene Scan", _run_secret_scan),
    ]

    all_passed = True
    sections: list[str] = [
        "=== DAO DEN LONG VERIFICATION REPORT ===",
        f"Timestamp (UTC): {timestamp}",
        f"Mode: {mode}",
        f"Phase: {args.phase}",
        f"Git HEAD: {git_rev}",
        f"Python: {platform.python_version()} ({sys.executable})",
        f"Platform: {platform.platform()}",
        "",
    ]

    for title, fn in checks:
        ok, detail = fn()
        status = "PASS" if ok else "FAIL"
        all_passed = all_passed and ok
        sections.append(f"--- [{status}] {title} ---")
        sections.append(detail)
        sections.append("")

    sections.append(f"OVERALL RESULT: {'PASS' if all_passed else 'FAIL'}")
    report = "\n".join(sections) + "\n"
    print(report, end="")

    if args.write_proof:
        proof_dir = ROOT_DIR / "docs" / "proof" / args.phase
        proof_dir.mkdir(parents=True, exist_ok=True)
        proof_file = proof_dir / "verify-output.txt"
        proof_file.write_text(report, encoding="utf-8", newline="\n")
        print(f"Saved real verification proof to {proof_file.relative_to(ROOT_DIR).as_posix()}")

    return 0 if all_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
