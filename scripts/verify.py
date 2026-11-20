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
import tempfile

ROOT_DIR = Path(__file__).resolve().parent.parent

SECRET_PATTERNS = (
    ("OpenAI/API token", re.compile(r"sk-[A-Za-z0-9]{20,}")),
    ("GitHub token", re.compile(r"ghp_[A-Za-z0-9]{20,}")),
    ("Google API key", re.compile(r"AIza[0-9A-Za-z_-]{20,}")),
    ("AWS access key", re.compile(r"AKIA[0-9A-Z]{16}")),
)

IGNORED_DIRS = {".git", "__pycache__", ".pytest_cache", ".venv", "venv", "node_modules"}

REQUIRED_TUNING_KEYS = {
    "player_speed",
    "carry_capacity",
    "lantern_cost",
    "lantern_count_night1",
    "pickup_radius",
    "interact_radius",
    "pulse_cost",
    "pulse_radius",
    "night1_duration_s",
    "flames",
    "invuln_s",
    "hit_drop_ratio",
    "pulse_stun_s",
    "pulse_push_m",
    "pulse_cooldown_s",
    "safe_radius",
    "shade_speed",
    "shade_hit_radius",
    "fall_enabled",
    "score",
}


def _git_head_short() -> str:
    proc = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=ROOT_DIR,
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.stdout.strip() if proc.returncode == 0 else "uncommitted"


def _run_contract_check() -> tuple[bool, str]:
    contract_path = ROOT_DIR / "game.contract.json"
    if not contract_path.is_file():
        return False, "Missing game.contract.json at repository root."
    try:
        data = json.loads(contract_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return False, f"Invalid game.contract.json: {exc}"

    missing_top = {"contract_version", "team", "build_cmd", "run_cmd", "headless_cmd", "tuning"} - set(data)
    if missing_top:
        return False, f"game.contract.json missing top-level keys: {sorted(missing_top)}"
    missing_tuning = REQUIRED_TUNING_KEYS - set(data["tuning"])
    if missing_tuning:
        return False, f"game.contract.json missing tuning keys: {sorted(missing_tuning)}"

    return True, (
        f"contract_version={data['contract_version']}, team={data['team']}, "
        f"lanterns={data['tuning']['lantern_count_night1']}, "
        f"headless_cmd='{data['headless_cmd']}'"
    )


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
    scenarios_dir = ROOT_DIR / "tests" / "scenarios"
    lines: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        cases = [
            (
                "win_scenario",
                [
                    sys.executable, "run.py", "headless",
                    "--seed", "42", "--night", "1",
                    "--scenario", str(scenarios_dir / "win_scenario.json"),
                    "--inputs", str(scenarios_dir / "win_inputs.json"),
                    "--ticks", "600",
                ],
            ),
            (
                "default_night1",
                [
                    sys.executable, "run.py", "headless",
                    "--seed", "777", "--night", "1",
                    "--ticks", "300",
                ],
            ),
        ]

        for label, base_cmd in cases:
            out1 = tmp_dir / f"{label}_1.jsonl"
            out2 = tmp_dir / f"{label}_2.jsonl"
            r1 = subprocess.run([*base_cmd, "--out", str(out1)], cwd=ROOT_DIR, capture_output=True, check=False)
            r2 = subprocess.run([*base_cmd, "--out", str(out2)], cwd=ROOT_DIR, capture_output=True, check=False)
            if r1.returncode != 0 or r2.returncode != 0:
                err = (r1.stderr + r2.stderr).decode("utf-8", errors="replace")
                return False, f"{label} failed ({r1.returncode}, {r2.returncode}):\n{err}"

            b1 = out1.read_bytes()
            b2 = out2.read_bytes()
            h1 = hashlib.sha256(b1).hexdigest()
            h2 = hashlib.sha256(b2).hexdigest()
            if b1 != b2:
                return False, f"{label} nondeterministic: {h1} != {h2}"

            records = [json.loads(line) for line in b1.decode("utf-8").splitlines() if line.strip()]
            end_rec = records[-1]
            lines.append(
                f"[{label}] SHA-256={h1} | lines={len(records)} | "
                f"end=(state={end_rec.get('state')}, ticks={end_rec.get('ticks')}, score={end_rec.get('score')})"
            )

    return True, "\n".join(lines)


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
    parser = argparse.ArgumentParser(description="Verify Dao Den Long build, contract, tests, determinism, and hygiene.")
    parser.add_argument("--quick", action="store_true", help="Run fast gate checks (for pre-commit/hooks)")
    parser.add_argument("--ci", action="store_true", help="Run CI verification with environment metadata")
    parser.add_argument("--phase", default="phase-1", help="Phase name for proof directory (default: phase-1)")
    parser.add_argument("--write-proof", action="store_true", help="Write raw output to docs/proof/<phase>/verify-output.txt")
    args = parser.parse_args(argv)

    mode = "quick" if args.quick else ("ci" if args.ci else "standard")
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    git_rev = _git_head_short()

    checks = [
        ("Test Contract v1.0 Schema (game.contract.json)", _run_contract_check),
        ("Unit & Contract Tests (unittest)", _run_unit_tests),
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
