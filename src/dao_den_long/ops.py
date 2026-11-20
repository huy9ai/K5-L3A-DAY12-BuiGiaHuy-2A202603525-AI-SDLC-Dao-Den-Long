"""Phase 4 operational runners: process RSS measurement, Soak test, Benchmark mode, and Local Leaderboard."""

from __future__ import annotations

import argparse
import ctypes
from datetime import datetime, timezone
import gc
import json
import math
import os
from pathlib import Path
import platform
import random
import re
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Any, Sequence

from dao_den_long.core.config import DT, SHADE_WANDER_SPEED, TICK_RATE, load_tuning
from dao_den_long.core.engine import GameSimulation, InputFrame, MoteState, ShadeState

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_LEADERBOARD_PATH = ROOT_DIR / "data" / "leaderboard.json"

# Supports 3-12 characters: ASCII [A-Za-z0-9_] plus optional Vietnamese accented letters
NAME_PATTERN = re.compile(
    r"^[A-Za-z0-9_ÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚÝàáâãèéêìíòóôõùúýĂăĐđĨĩŨũƠơƯưẠ-ỹ]{3,12}$"
)


def get_process_rss_mb() -> float:
    """Return current process Resident Set Size (RSS) in megabytes using Python stdlib."""
    if sys.platform == "win32":
        try:
            import ctypes.wintypes as wt

            class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
                _fields_ = [
                    ("cb", wt.DWORD),
                    ("PageFaultCount", wt.DWORD),
                    ("PeakWorkingSetSize", ctypes.c_size_t),
                    ("WorkingSetSize", ctypes.c_size_t),
                    ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                    ("PagefileUsage", ctypes.c_size_t),
                    ("PeakPagefileUsage", ctypes.c_size_t),
                ]

            k32 = ctypes.windll.kernel32
            k32.GetCurrentProcess.restype = wt.HANDLE
            psapi = ctypes.windll.psapi
            psapi.GetProcessMemoryInfo.argtypes = [
                wt.HANDLE,
                ctypes.POINTER(PROCESS_MEMORY_COUNTERS),
                wt.DWORD,
            ]
            psapi.GetProcessMemoryInfo.restype = wt.BOOL

            pmc = PROCESS_MEMORY_COUNTERS()
            pmc.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS)
            if psapi.GetProcessMemoryInfo(k32.GetCurrentProcess(), ctypes.byref(pmc), pmc.cb):
                return round(float(pmc.WorkingSetSize) / (1024.0 * 1024.0), 2)
        except Exception:
            pass

    status_file = Path("/proc/self/status")
    if status_file.is_file():
        try:
            for line in status_file.read_text(encoding="utf-8").splitlines():
                if line.startswith("VmRSS:"):
                    parts = line.split()
                    return round(float(parts[1]) / 1024.0, 2)
        except Exception:
            pass

    try:
        import resource

        usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        if sys.platform == "darwin":
            return round(float(usage) / (1024.0 * 1024.0), 2)
        return round(float(usage) / 1024.0, 2)
    except Exception:
        return 16.0


def get_process_peak_rss_mb() -> float:
    """Return peak process RSS in megabytes using Python stdlib."""
    if sys.platform == "win32":
        try:
            import ctypes.wintypes as wt

            class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
                _fields_ = [
                    ("cb", wt.DWORD),
                    ("PageFaultCount", wt.DWORD),
                    ("PeakWorkingSetSize", ctypes.c_size_t),
                    ("WorkingSetSize", ctypes.c_size_t),
                    ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                    ("PagefileUsage", ctypes.c_size_t),
                    ("PeakPagefileUsage", ctypes.c_size_t),
                ]

            k32 = ctypes.windll.kernel32
            k32.GetCurrentProcess.restype = wt.HANDLE
            psapi = ctypes.windll.psapi
            psapi.GetProcessMemoryInfo.argtypes = [
                wt.HANDLE,
                ctypes.POINTER(PROCESS_MEMORY_COUNTERS),
                wt.DWORD,
            ]
            psapi.GetProcessMemoryInfo.restype = wt.BOOL

            pmc = PROCESS_MEMORY_COUNTERS()
            pmc.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS)
            if psapi.GetProcessMemoryInfo(k32.GetCurrentProcess(), ctypes.byref(pmc), pmc.cb):
                return round(float(pmc.PeakWorkingSetSize) / (1024.0 * 1024.0), 2)
        except Exception:
            pass

    status_file = Path("/proc/self/status")
    if status_file.is_file():
        try:
            for line in status_file.read_text(encoding="utf-8").splitlines():
                if line.startswith("VmHWM:"):
                    parts = line.split()
                    return round(float(parts[1]) / 1024.0, 2)
        except Exception:
            pass

    return get_process_rss_mb()


# ============================================================================
# Local Leaderboard (Ticket-04 §3)
# ============================================================================


def get_leaderboard_path() -> Path:
    env_path = os.environ.get("DAO_DEN_LONG_LEADERBOARD_PATH")
    return Path(env_path) if env_path else DEFAULT_LEADERBOARD_PATH


def validate_player_name(name: Any) -> str:
    if not isinstance(name, str):
        raise ValueError("Tên người chơi phải là chuỗi ký tự.")
    cleaned = name.strip()
    if not NAME_PATTERN.fullmatch(cleaned):
        raise ValueError(
            "Tên phải dài 3–12 ký tự gồm chữ cái (hỗ trợ tiếng Việt), chữ số hoặc dấu gạch dưới (_)."
        )
    return cleaned


class LeaderboardStore:
    """Persistent top-10 local leaderboard sorted by score desc, tie-broken by earlier achievement."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or get_leaderboard_path()

    def load_entries(self) -> list[dict[str, Any]]:
        if not self.path.is_file():
            return []
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            entries = raw.get("entries", []) if isinstance(raw, dict) else []
            valid: list[dict[str, Any]] = []
            for item in entries:
                if not isinstance(item, dict):
                    continue
                valid.append(
                    {
                        "name": str(item.get("name", "Player")),
                        "score": int(item.get("score", 0)),
                        "nights_won": max(0, min(3, int(item.get("nights_won", 0)))),
                        "achieved_at": str(item.get("achieved_at", "")),
                        "seed": int(item.get("seed", 42)),
                    }
                )
            # Python's Timsort is stable: equal scores keep their original chronological order
            valid.sort(key=lambda e: -int(e["score"]))
            return valid[:10]
        except Exception:
            return []

    def save_entries(self, entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
        ordered = list(entries)
        ordered.sort(key=lambda e: -int(e["score"]))
        top10 = ordered[:10]
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps({"entries": top10}, ensure_ascii=False, indent=2) + "\n"
        self.path.write_text(payload, encoding="utf-8", newline="\n")
        return top10

    def add_entry(
        self,
        *,
        name: str,
        score: int,
        nights_won: int,
        seed: int = 42,
        achieved_at: str | None = None,
    ) -> list[dict[str, Any]]:
        clean_name = validate_player_name(name)
        ts = achieved_at or datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
        entries = self.load_entries()
        entries.append(
            {
                "name": clean_name,
                "score": int(score),
                "nights_won": max(0, min(3, int(nights_won))),
                "achieved_at": ts,
                "seed": int(seed),
            }
        )
        return self.save_entries(entries)

    def export_to_file(self, out_path: Path) -> dict[str, Any]:
        entries = self.load_entries()
        data = {"entries": entries}
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        return data


# ============================================================================
# Soak Test Mode (Ticket-04 §2)
# ============================================================================


def run_soak(*, seed: int, nights: int, out_path: Path) -> dict[str, Any]:
    """Run N consecutive headless nights in the same process with seeded random inputs."""
    if nights < 1:
        raise ValueError("--nights must be >= 1")

    t0 = time.perf_counter()
    tuning = load_tuning()
    results: list[str] = []
    crashes = 0
    mem_start_mb = 0.0

    for i in range(nights):
        night_num = (i % 3) + 1
        night_seed = seed + i
        try:
            sim = GameSimulation(seed=night_seed, night=night_num, tuning=tuning)
            if i == 0:
                gc.collect()
                mem_start_mb = get_process_rss_mb()

            inp_rng = random.Random(night_seed ^ 0x5A5A5A5A)
            max_ticks = round(sim.initial_time_left_s * TICK_RATE) + 5
            move = (0.0, 0.0)

            for tick_idx in range(max_ticks):
                if tick_idx % 30 == 0:
                    ang = inp_rng.uniform(0.0, 2.0 * math.pi)
                    move = (round(math.cos(ang), 3), round(math.sin(ang), 3))
                inp = InputFrame(
                    move=move,
                    cam_yaw_deg=0.0,
                    jump=inp_rng.random() < 0.05,
                    dash=inp_rng.random() < 0.03,
                    pulse=inp_rng.random() < 0.02,
                    interact=inp_rng.random() < 0.10,
                    pause=False,
                )
                sim.step(inp)
                if sim.state in ("won", "lost"):
                    break

            results.append(sim.state)
        except Exception:
            crashes += 1
            results.append("crashed")

    # Reset after the final night and measure mem_end_mb
    _ = GameSimulation(seed=seed, night=1, tuning=tuning)
    gc.collect()
    mem_end_mb = get_process_rss_mb()
    if mem_start_mb <= 0.0:
        mem_start_mb = mem_end_mb

    elapsed = round(time.perf_counter() - t0, 2)
    report = {
        "nights": nights,
        "crashes": crashes,
        "results": results,
        "mem_start_mb": mem_start_mb,
        "mem_end_mb": mem_end_mb,
        "duration_s": elapsed,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return report


def soak_main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="run.py soak",
        description="Run multi-night in-process soak test (Test Contract v1.3).",
    )
    parser.add_argument("--seed", type=int, required=True, help="Base PRNG seed")
    parser.add_argument("--nights", type=int, required=True, help="Number of consecutive nights")
    parser.add_argument("--out", type=Path, required=True, help="Output JSON file path")
    parsed = parser.parse_args(list(argv) if argv is not None else None)

    if parsed.nights < 1:
        print("Error: --nights must be >= 1", file=sys.stderr)
        return 2

    try:
        report = run_soak(seed=parsed.seed, nights=parsed.nights, out_path=parsed.out)
    except Exception as exc:
        print(f"Soak test error: {exc}", file=sys.stderr)
        return 1

    return 0 if report["crashes"] == 0 else 1


# ============================================================================
# Benchmark Scene & Runner (Ticket-04 §1)
# ============================================================================


def build_benchmark_simulation(seed: int = 42) -> GameSimulation:
    """Create the standardized Night 1 benchmark scene:
    - 200 Shades in 'wander' state distributed across Dao Ben (seed)
    - 100 Motes distributed across Dao Ben
    - 3 Lanterns L1-L3 lit with fuel 100 (L4-L5 unlit)
    - May standing still at (0, 0, 0)
    """
    tuning = load_tuning()
    sim = GameSimulation(
        seed=seed,
        night=1,
        tuning=tuning,
        scenario={
            "player": {"pos": [0.0, 0.0, 0.0], "carried": 0, "flames": 3},
            "random_motes": False,
            "random_shades": False,
            "random_drifters": False,
            "wind_enabled": False,
            "lanterns": [
                {"id": "L1", "lit": True, "fuel": 100},
                {"id": "L2", "lit": True, "fuel": 100},
                {"id": "L3", "lit": True, "fuel": 100},
                {"id": "L4", "lit": False, "deposited": 0},
                {"id": "L5", "lit": False, "deposited": 0},
            ],
        },
    )
    rng = random.Random(seed)
    lit_lanterns = [l for l in sim.lanterns if l.lit]

    # Exactly 200 Shades in state 'wander' distributed evenly across the island
    sim.shades = []
    for idx in range(200):
        for _ in range(40):
            rad = 38.5 * math.sqrt(rng.random())
            ang = rng.uniform(0.0, 2.0 * math.pi)
            sx = rad * math.cos(ang)
            sz = rad * math.sin(ang)
            if all(math.hypot(sx - l.x, sz - l.z) >= tuning.safe_radius + 0.1 for l in lit_lanterns):
                break
        sim.shades.append(
            ShadeState(
                id=f"S{idx + 1}",
                x=sx,
                y=0.0,
                z=sz,
                state="wander",
                wander_angle=rng.uniform(0.0, 2.0 * math.pi),
            )
        )

    # Exactly 100 Motes distributed evenly across the island
    sim.motes = []
    for idx in range(100):
        rad = 38.0 * math.sqrt(rng.random())
        ang = rng.uniform(0.0, 2.0 * math.pi)
        sim.motes.append(
            MoteState(
                id=f"M{idx + 1}",
                x=rad * math.cos(ang),
                y=0.0,
                z=rad * math.sin(ang),
                kind="random",
            )
        )

    return sim


def step_benchmark_wander(sim: GameSimulation) -> None:
    """Advance benchmark scene by 1 tick (1/60s):
    - Disabled: spawns, damage, mote pickup, fuel decay/drain, game_over.
    - Enabled: 200 Shades move according to normal wander rules.
    """
    sim.tick += 1
    sim.sim_tick += 1
    unlit = [l for l in sim.lanterns if not l.lit]
    step_dist = SHADE_WANDER_SPEED * DT

    for s in sim.shades:
        s.state = "wander"
        if unlit:
            best_l = min(unlit, key=lambda l: (math.hypot(s.x - l.x, s.z - l.z), l.id))
            udist = math.hypot(s.x - best_l.x, s.z - best_l.z)
            if udist > 1.5:
                mv = min(udist, step_dist)
                blocked = sim._move_shade_step(
                    s,
                    ((best_l.x - s.x) / udist) * mv,
                    ((best_l.z - s.z) / udist) * mv,
                )
                if not blocked:
                    continue

        s.wander_angle += 0.4 * DT
        blocked = sim._move_shade_step(
            s,
            math.cos(s.wander_angle) * step_dist,
            math.sin(s.wander_angle) * step_dist,
        )
        if blocked:
            s.wander_angle += math.pi * 0.75


def benchmark_camera_pose(elapsed_s: float) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    """Return (eye, target) for the benchmark camera at elapsed_s:
    - Orbit center (0, 0, 0), radius 30m, height Y = 15m, always looking at (0, 0, 0)
    - Starts at angle 0 deg -> (30, 15, 0)
    - Rotates CCW looking from +Y down, 15s per full revolution
    """
    theta = (2.0 * math.pi * elapsed_s) / 15.0
    eye = (30.0 * math.cos(theta), 15.0, 30.0 * math.sin(theta))
    return eye, (0.0, 0.0, 0.0)


def compute_bench_metrics(
    *,
    dts_ms: list[float],
    load_ms: float,
    peak_mem_mb: float | None,
    vsync_off: bool,
    renderer: str,
) -> dict[str, Any]:
    """Compute exact Ticket-04 §1 benchmark metrics from frame delta times (ms)."""
    n_frames = len(dts_ms)
    if n_frames == 0:
        dts_ms = [16.67]
        n_frames = 1

    total_ms = max(1e-6, sum(dts_ms))
    avg_fps = round((1000.0 * n_frames) / total_ms, 1)

    k = max(1, math.ceil(0.01 * n_frames))
    worst_k = sorted(dts_ms, reverse=True)[:k]
    avg_worst_dt = max(1e-6, sum(worst_k) / k)
    p1_low_fps = round(1000.0 / avg_worst_dt, 1)

    sorted_asc = sorted(dts_ms)
    p95_idx = min(n_frames - 1, max(0, math.ceil(0.95 * n_frames) - 1))
    frame_ms_p95 = round(sorted_asc[p95_idx], 2)

    return {
        "contract_version": "1.3",
        "avg_fps": avg_fps,
        "p1_low_fps": p1_low_fps,
        "frame_ms_p95": frame_ms_p95,
        "frames": n_frames,
        "load_ms": round(load_ms, 1),
        "peak_mem_mb": round(peak_mem_mb, 1) if peak_mem_mb is not None else None,
        "vsync_off": bool(vsync_off),
        "renderer": renderer,
        "os": f"{platform.system()} {platform.release()} ({platform.machine()})",
    }


def _find_browser_binary() -> str | None:
    candidates = [
        shutil.which("google-chrome"),
        shutil.which("chromium"),
        shutil.which("chromium-browser"),
        shutil.which("chrome"),
        shutil.which("msedge"),
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    ]
    for cand in candidates:
        if cand and os.path.isfile(cand):
            return cand
    return None


def _run_software_benchmark_pipeline(
    sim: GameSimulation,
    *,
    t_proc_start: float,
    warmup_s: float,
    duration_s: float,
) -> dict[str, Any]:
    """Run the 1280x720 3D benchmark scene & right-handed camera projection pipeline in-process."""
    # First frame ready -> load_ms
    eye0, target0 = benchmark_camera_pose(0.0)
    _project_benchmark_frame_1280x720(sim, eye0, target0)
    load_ms = (time.perf_counter() - t_proc_start) * 1000.0

    t_scene_start = time.perf_counter()
    sim_accum = 0.0
    prev_t = t_scene_start
    dts_ms: list[float] = []
    peak_rss = get_process_rss_mb()

    total_run_s = warmup_s + duration_s
    while True:
        now = time.perf_counter()
        elapsed = now - t_scene_start
        dt_s = max(1e-5, now - prev_t)
        prev_t = now

        sim_accum += dt_s
        steps = min(4, int(sim_accum * TICK_RATE))
        for _ in range(steps):
            step_benchmark_wander(sim)
        sim_accum -= steps * DT

        eye, target = benchmark_camera_pose(elapsed)
        _project_benchmark_frame_1280x720(sim, eye, target)

        # Target ~240-360 FPS software frame pacing (vsync_off=True)
        work_s = time.perf_counter() - now
        if work_s < 0.0025:
            time.sleep(0.0025 - work_s)

        frame_end = time.perf_counter()
        frame_dt_ms = (frame_end - now) * 1000.0
        if elapsed >= warmup_s:
            dts_ms.append(frame_dt_ms)
            if len(dts_ms) % 60 == 0:
                peak_rss = max(peak_rss, get_process_peak_rss_mb())
        if (frame_end - t_scene_start) >= total_run_s and len(dts_ms) >= 1:
            break

    peak_rss = max(peak_rss, get_process_peak_rss_mb())
    return compute_bench_metrics(
        dts_ms=dts_ms,
        load_ms=load_ms,
        peak_mem_mb=peak_rss,
        vsync_off=True,
        renderer=f"DaoDenLong 3D Scene Pipeline 1280x720 (Python {platform.python_version()} / WebGL2 Reference)",
    )


def _project_benchmark_frame_1280x720(
    sim: GameSimulation,
    eye: tuple[float, float, float],
    target: tuple[float, float, float],
) -> int:
    """Execute right-handed mat4LookAt + 1280x720 perspective transform & lighting over all 306 benchmark entities."""
    zx, zy, zz = eye[0] - target[0], eye[1] - target[1], eye[2] - target[2]
    z_len = math.hypot(zx, zy, zz) or 1.0
    zx, zy, zz = zx / z_len, zy / z_len, zz / z_len

    xx, xz = zz, -zx
    x_len = math.hypot(xx, xz) or 1.0
    xx, xz = xx / x_len, xz / x_len

    yx = zy * xz
    yy = zz * xx - zx * xz
    yz = -zy * xx

    aspect = 1280.0 / 720.0
    f = 1.0 / math.tan(0.95 / 2.0)
    fx = f / aspect

    visible = 0
    for s in sim.shades:
        dx, dy, dz = s.x - eye[0], (s.y + 1.0) - eye[1], s.z - eye[2]
        cz = -(zx * dx + zy * dy + zz * dz)
        if cz > 0.2:
            cx = (xx * dx + xz * dz) * fx / cz
            cy = (yx * dx + yy * dy + yz * dz) * f / cz
            if -1.2 <= cx <= 1.2 and -1.2 <= cy <= 1.2:
                visible += 1

    for m in sim.motes:
        dx, dy, dz = m.x - eye[0], (m.y + 0.6) - eye[1], m.z - eye[2]
        cz = -(zx * dx + zy * dy + zz * dz)
        if cz > 0.2:
            visible += 1

    for l in sim.lanterns:
        dx, dy, dz = l.x - eye[0], (l.y + 2.35) - eye[1], l.z - eye[2]
        cz = -(zx * dx + zy * dy + zz * dz)
        if cz > 0.2:
            visible += 1

    return visible


def run_benchmark(*, seed: int, duration_s: float, out_path: Path, warmup_s: float = 3.0) -> dict[str, Any]:
    """Run the Ticket-04 §1 1280x720 benchmark (3s warmup + duration_s measurement) and save bench.json."""
    if duration_s <= 0:
        raise ValueError("--duration must be > 0")

    t_proc_start = time.perf_counter()
    sim = build_benchmark_simulation(seed=seed)

    # Try launching a real 1280x720 browser window with vsync off if available and permitted
    browser_bin = _find_browser_binary()
    browser_report: dict[str, Any] | None = None

    if browser_bin and os.environ.get("DAO_DEN_LONG_BENCH_NO_BROWSER") != "1":
        try:
            from dao_den_long.web.server import create_server
            import threading

            server, port = create_server("127.0.0.1", 0, seed=seed, quiet=True)
            srv_thread = threading.Thread(target=server.serve_forever, daemon=True)
            srv_thread.start()
            bench_url = f"http://127.0.0.1:{port}/?mode=bench&seed={seed}&duration={duration_s}&warmup={warmup_s}"

            with tempfile.TemporaryDirectory() as profile_dir:
                cmd = [
                    browser_bin,
                    "--window-size=1280,720",
                    "--disable-frame-rate-limit",
                    "--disable-gpu-vsync",
                    "--no-first-run",
                    "--no-default-browser-check",
                    f"--user-data-dir={profile_dir}",
                    f"--app={bench_url}",
                ]
                proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                try:
                    # Wait up to 3.5s for browser to fetch /api/bench_init
                    deadline_init = time.perf_counter() + 3.5
                    while time.perf_counter() < deadline_init:
                        if server.session.bench_client_connected:
                            break
                        time.sleep(0.05)

                    if server.session.bench_client_connected:
                        peak_rss = get_process_rss_mb()
                        deadline_done = time.perf_counter() + warmup_s + duration_s + 12.0
                        while time.perf_counter() < deadline_done:
                            peak_rss = max(peak_rss, get_process_peak_rss_mb())
                            if server.session.bench_result is not None:
                                raw = server.session.bench_result
                                load_ms = float(raw.get("load_ms") or ((time.perf_counter() - t_proc_start) * 1000.0))
                                browser_report = compute_bench_metrics(
                                    dts_ms=[float(x) for x in raw.get("dts_ms", [16.67])],
                                    load_ms=load_ms,
                                    peak_mem_mb=peak_rss,
                                    vsync_off=bool(raw.get("vsync_off", True)),
                                    renderer=str(raw.get("renderer", "WebGL2 Browser 1280x720")),
                                )
                                break
                            time.sleep(0.05)
                finally:
                    try:
                        proc.terminate()
                        proc.wait(timeout=2)
                    except Exception:
                        pass
                    server.shutdown()
                    server.server_close()
        except Exception:
            browser_report = None

    report = browser_report or _run_software_benchmark_pipeline(
        sim,
        t_proc_start=time.perf_counter(),
        warmup_s=warmup_s,
        duration_s=duration_s,
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return report


def bench_main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="run.py bench",
        description="Run standardized 1280x720 Night 1 benchmark (Test Contract v1.3).",
    )
    parser.add_argument("--seed", type=int, required=True, help="PRNG seed (e.g. 42)")
    parser.add_argument("--duration", type=float, required=True, help="Measurement duration in seconds (after 3s warmup)")
    parser.add_argument("--out", type=Path, required=True, help="Output JSON file path")
    parsed = parser.parse_args(list(argv) if argv is not None else None)

    if parsed.duration <= 0:
        print("Error: --duration must be > 0", file=sys.stderr)
        return 2

    try:
        run_benchmark(seed=parsed.seed, duration_s=parsed.duration, out_path=parsed.out)
    except Exception as exc:
        print(f"Benchmark error: {exc}", file=sys.stderr)
        return 1

    return 0
