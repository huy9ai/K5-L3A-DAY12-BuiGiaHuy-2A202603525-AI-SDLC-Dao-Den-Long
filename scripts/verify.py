"""Single-command verification gate, 3-Night determinism check, benchmark, soak check, and proof generator (v1.3)."""

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
import time

ROOT_DIR = Path(__file__).resolve().parent.parent

SECRET_PATTERNS = (
    ("OpenAI/API token", re.compile(r"sk-[A-Za-z0-9]{20,}")),
    ("GitHub token", re.compile(r"ghp_[A-Za-z0-9]{20,}")),
    ("Google API key", re.compile(r"AIza[0-9A-Za-z_-]{20,}")),
    ("AWS access key", re.compile(r"AKIA[0-9A-Z]{16}")),
)

IGNORED_DIRS = {".git", "__pycache__", ".pytest_cache", ".venv", "venv", "node_modules"}

REQUIRED_TOP_KEYS = {
    "contract_version",
    "team",
    "build_cmd",
    "run_cmd",
    "headless_cmd",
    "bench_cmd",
    "soak_cmd",
    "tuning",
}

REQUIRED_TUNING_KEYS = {
    "player_speed",
    "dash_speed",
    "dash_duration_s",
    "dash_cooldown_s",
    "carry_capacity",
    "capacity_max",
    "lantern_cost",
    "relight_cost",
    "lantern_count_night1",
    "pickup_radius",
    "interact_radius",
    "pulse_cost",
    "pulse_radius",
    "night1_duration_s",
    "night2_duration_s",
    "night3_duration_s",
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
    "fuel_max",
    "fuel_decay_per_s",
    "fuel_per_mote",
    "win_ratio",
    "drain_per_s",
    "low_fuel_threshold",
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

    missing_top = REQUIRED_TOP_KEYS - set(data)
    if missing_top:
        return False, f"game.contract.json missing top-level keys: {sorted(missing_top)}"
    if data["contract_version"] != "1.3":
        return False, f"Expected contract_version '1.3', got '{data['contract_version']}'"
    missing_tuning = REQUIRED_TUNING_KEYS - set(data["tuning"])
    if missing_tuning:
        return False, f"game.contract.json missing tuning keys: {sorted(missing_tuning)}"

    t = data["tuning"]
    return True, (
        f"contract_version={data['contract_version']}, team={data['team']}, "
        f"bench_cmd='{data['bench_cmd']}', soak_cmd='{data['soak_cmd']}', "
        f"fuel_max={t['fuel_max']}, win_ratio={t['win_ratio']}, capacity_max={t['capacity_max']}"
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
                "night1_dawn_win",
                [
                    sys.executable, "run.py", "headless",
                    "--seed", "42", "--night", "1",
                    "--scenario", str(scenarios_dir / "win_scenario.json"),
                    "--inputs", str(scenarios_dir / "win_inputs.json"),
                    "--ticks", "600",
                ],
            ),
            (
                "night1_p3_fuel_relight",
                [
                    sys.executable, "run.py", "headless",
                    "--seed", "42", "--night", "1",
                    "--scenario", str(scenarios_dir / "p3_fuel_relight_refuel_scenario.json"),
                    "--inputs", str(scenarios_dir / "p3_fuel_relight_refuel_inputs.json"),
                    "--ticks", "700",
                ],
            ),
            (
                "night1_p3_shade_drain",
                [
                    sys.executable, "run.py", "headless",
                    "--seed", "42", "--night", "1",
                    "--scenario", str(scenarios_dir / "p3_shade_drain_scenario.json"),
                    "--inputs", str(scenarios_dir / "p3_shade_drain_inputs.json"),
                    "--ticks", "400",
                ],
            ),
            (
                "night2_drifter_charm",
                [
                    sys.executable, "run.py", "headless",
                    "--seed", "42", "--night", "2",
                    "--scenario", str(scenarios_dir / "p2_night2_pad_charm_drifter_scenario.json"),
                    "--inputs", str(scenarios_dir / "p2_night2_pad_charm_drifter_inputs.json"),
                    "--ticks", "80",
                ],
            ),
            (
                "night3_ramp_wind",
                [
                    sys.executable, "run.py", "headless",
                    "--seed", "42", "--night", "3",
                    "--scenario", str(scenarios_dir / "p2_night3_tiers_wind_scenario.json"),
                    "--inputs", str(scenarios_dir / "p2_night3_tiers_wind_inputs.json"),
                    "--ticks", "80",
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


def _run_full_night_benchmark() -> tuple[bool, str]:
    perf_scenario = ROOT_DIR / "tests" / "scenarios" / "p2_perf_21600_scenario.json"
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "bench_n3.jsonl"
        cmd = [
            sys.executable, "run.py", "headless",
            "--seed", "42", "--night", "3",
            "--scenario", str(perf_scenario),
            "--ticks", "21600", "--out", str(out),
        ]
        t0 = time.perf_counter()
        proc = subprocess.run(cmd, cwd=ROOT_DIR, capture_output=True, check=False)
        elapsed = time.perf_counter() - t0
        if proc.returncode != 0:
            return False, proc.stderr.decode("utf-8", errors="replace")
        lines = out.read_text(encoding="utf-8").splitlines()
        end_rec = json.loads(lines[-1])
        ok = elapsed <= 30.0 and end_rec.get("ticks") == 21600
        return ok, (
            f"Night 3 stress {end_rec.get('ticks')}-tick headless (with motes+shades+drifters+wind+fuel) "
            f"completed in {elapsed:.3f}s (limit <= 30.0s), lines={len(lines)}"
        )


def _run_bench_and_soak_artifacts_check() -> tuple[bool, str]:
    bench_path = ROOT_DIR / "bench.json"
    soak_path = ROOT_DIR / "soak.json"
    if not bench_path.is_file() or not soak_path.is_file():
        return False, "Missing committed bench.json or soak.json at repository root."

    try:
        b = json.loads(bench_path.read_text(encoding="utf-8"))
        s = json.loads(soak_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return False, f"Invalid bench.json or soak.json: {exc}"

    req_b = {
        "contract_version",
        "avg_fps",
        "p1_low_fps",
        "frame_ms_p95",
        "frames",
        "load_ms",
        "peak_mem_mb",
        "vsync_off",
        "renderer",
        "os",
    }
    if req_b - set(b):
        return False, f"bench.json missing keys: {sorted(req_b - set(b))}"
    if b["contract_version"] != "1.3":
        return False, f"bench.json contract_version={b['contract_version']} != 1.3"
    if float(b["avg_fps"]) < 60.0 or float(b["p1_low_fps"]) < 30.0 or float(b["load_ms"]) > 10000.0:
        return False, f"bench.json below threshold: {b}"

    req_s = {"nights", "crashes", "results", "mem_start_mb", "mem_end_mb", "duration_s"}
    if req_s - set(s):
        return False, f"soak.json missing keys: {sorted(req_s - set(s))}"
    if int(s["nights"]) != 10 or int(s["crashes"]) != 0 or len(s["results"]) != 10:
        return False, f"soak.json invalid night results: {s}"
    if float(s["mem_end_mb"]) > 1.2 * float(s["mem_start_mb"]):
        return False, f"soak.json memory growth exceeded 1.2x: {s}"

    return True, (
        f"bench.json: avg_fps={b['avg_fps']}, p1_low_fps={b['p1_low_fps']}, "
        f"frame_ms_p95={b['frame_ms_p95']}ms, frames={b['frames']}, load_ms={b['load_ms']}ms, "
        f"peak_mem_mb={b['peak_mem_mb']}MB | "
        f"soak.json: nights={s['nights']}, crashes={s['crashes']}, "
        f"mem={s['mem_start_mb']}->{s['mem_end_mb']}MB, duration_s={s['duration_s']}s"
    )


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

        if file_path.suffix.lower() in {".png", ".jpg", ".gif", ".mp4", ".pyc", ".ico", ".zip"}:
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
    parser = argparse.ArgumentParser(description="Verify Dao Den Long build, contract v1.3, tests, determinism, bench/soak, and perf.")
    parser.add_argument("--quick", action="store_true", help="Run fast gate checks (for pre-commit/hooks)")
    parser.add_argument("--ci", action="store_true", help="Run CI verification with environment metadata")
    parser.add_argument("--phase", default="phase-4", help="Phase name for proof directory (default: phase-4)")
    parser.add_argument("--write-proof", action="store_true", help="Write raw output to docs/proof/<phase>/verify-output.txt")
    args = parser.parse_args(argv)

    mode = "quick" if args.quick else ("ci" if args.ci else "standard")
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    git_rev = _git_head_short()

    checks = [
        ("Test Contract v1.3 Schema (game.contract.json)", _run_contract_check),
        ("Unit, Regression & Phase 4 Tests (unittest)", _run_unit_tests),
        ("3-Night + Phase 3 Headless Determinism (SHA-256 x2)", _run_headless_determinism),
        ("Committed bench.json & soak.json Threshold Check", _run_bench_and_soak_artifacts_check),
    ]
    if not args.quick:
        checks.append(("Full-Night Headless Benchmark (21,600 ticks <= 30s)", _run_full_night_benchmark))
    checks.append(("Secret & Hygiene Scan", _run_secret_scan))

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
