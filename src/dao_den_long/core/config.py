"""Single-source-of-truth configuration loader synced with game.contract.json (v1.2)."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[3]
DEFAULT_CONTRACT_PATH = ROOT_DIR / "game.contract.json"

TICK_RATE = 60
DT = 1.0 / TICK_RATE

# Standardized Ticket-02 & Ticket-03 gameplay constants (60 Hz, meters, seconds, Y up)
JUMP_VELOCITY = 7.0
GRAVITY = 20.0
FALL_Y_THRESHOLD = -10.0
RESPAWN_WAIT_TICKS = 60
INVULN_TICKS = 90

SHADE_DETECT_RADIUS = 12.0
SHADE_LEASH_RADIUS = 18.0
SHADE_WANDER_SPEED = 2.0
SHADE_SPAWN_TICKS = 30
SHADE_RECOIL_DIST = 2.0
SHADE_RECOIL_TICKS = 60
SHADE_DRAIN_RADIUS = 2.0
SHADE_DRAIN_DETECT_PLAYER_RADIUS = 6.0
FUEL_DRAIN_EVENT_INTERVAL_TICKS = 60
SAFE_PUSHOUT_MAX_TICKS = 30
VALID_SHADE_STATES = ("spawning", "wander", "chase", "recoil", "stunned", "drain")

SCORE_RELIGHT = 40
SCORE_STUN_DRAINING_TOTAL = 15
SCORE_DAWN_LANTERN_BASE = 50

PULSE_CENTER_Y_OFFSET = 0.8
PULSE_PUSH_TICKS = 15

MOTE_INIT_COUNT = 20
MOTE_CAP = 30
MOTE_SPAWN_INTERVAL_TICKS = 240
DROPPED_MOTE_TTL_TICKS = 480
ENTITY_MAX_HEIGHT_DIFF = 1.5

CHARM_SPEED = 7.2
CHARM_DURATION_TICKS = 600
CHARM_RESPAWN_TICKS = 2700

DRIFTER_IDLE_SPEED = 2.0
DRIFTER_CHASE_SPEED = 7.0
DRIFTER_FLEE_SPEED = 7.0
DRIFTER_DETECT_RADIUS = 15.0
DRIFTER_STEAL_RADIUS = 1.2
DRIFTER_STEAL_MIN_CARRIED = 5
DRIFTER_STEAL_MAX = 3
DRIFTER_FLEE_TICKS = 240
DRIFTER_DROP_FLEE_TICKS = 120
DRIFTER_SPAWN_INTERVAL_TICKS = 1200
DRIFTER_MAX = 2

WIND_INTERVAL_TICKS = 1800
WIND_WARN_TICKS = 120
WIND_DURATION_TICKS = 300
WIND_PUSH_SPEED = 2.0


@dataclass(frozen=True)
class ScoreTuning:
    """Scoring weights per Test Contract v1.2."""

    per_mote: int
    per_lantern: int
    per_stun: int
    per_second_left: int
    per_flame_left: int


@dataclass(frozen=True)
class TuningConfig:
    """Gameplay tuning parameters synced with game.contract.json (v1.2)."""

    player_speed: float
    dash_speed: float
    dash_duration_s: float
    dash_cooldown_s: float
    carry_capacity: int
    capacity_max: int
    lantern_cost: int
    relight_cost: int
    lantern_count_night1: int
    pickup_radius: float
    interact_radius: float
    pulse_cost: int
    pulse_radius: float
    night1_duration_s: float
    night2_duration_s: float
    night3_duration_s: float
    flames: int
    invuln_s: float
    hit_drop_ratio: float
    pulse_stun_s: float
    pulse_push_m: float
    pulse_cooldown_s: float
    safe_radius: float
    shade_speed: float
    shade_hit_radius: float
    fall_enabled: bool
    fuel_max: float
    fuel_decay_per_s: float
    fuel_per_mote: float
    win_ratio: float
    drain_per_s: float
    low_fuel_threshold: float
    score: ScoreTuning


def load_contract_data(contract_path: Path | None = None) -> dict[str, Any]:
    """Read raw game.contract.json payload."""
    path = contract_path or DEFAULT_CONTRACT_PATH
    return json.loads(path.read_text(encoding="utf-8"))


def load_tuning(contract_path: Path | None = None) -> TuningConfig:
    """Load TuningConfig from game.contract.json."""
    data = load_contract_data(contract_path)
    t = data["tuning"]
    s = t["score"]
    return TuningConfig(
        player_speed=float(t["player_speed"]),
        dash_speed=float(t["dash_speed"]),
        dash_duration_s=float(t["dash_duration_s"]),
        dash_cooldown_s=float(t["dash_cooldown_s"]),
        carry_capacity=int(t["carry_capacity"]),
        capacity_max=int(t["capacity_max"]),
        lantern_cost=int(t["lantern_cost"]),
        relight_cost=int(t["relight_cost"]),
        lantern_count_night1=int(t["lantern_count_night1"]),
        pickup_radius=float(t["pickup_radius"]),
        interact_radius=float(t["interact_radius"]),
        pulse_cost=int(t["pulse_cost"]),
        pulse_radius=float(t["pulse_radius"]),
        night1_duration_s=float(t["night1_duration_s"]),
        night2_duration_s=float(t["night2_duration_s"]),
        night3_duration_s=float(t["night3_duration_s"]),
        flames=int(t["flames"]),
        invuln_s=float(t["invuln_s"]),
        hit_drop_ratio=float(t["hit_drop_ratio"]),
        pulse_stun_s=float(t["pulse_stun_s"]),
        pulse_push_m=float(t["pulse_push_m"]),
        pulse_cooldown_s=float(t["pulse_cooldown_s"]),
        safe_radius=float(t["safe_radius"]),
        shade_speed=float(t["shade_speed"]),
        shade_hit_radius=float(t["shade_hit_radius"]),
        fall_enabled=bool(t["fall_enabled"]),
        fuel_max=float(t["fuel_max"]),
        fuel_decay_per_s=float(t["fuel_decay_per_s"]),
        fuel_per_mote=float(t["fuel_per_mote"]),
        win_ratio=float(t["win_ratio"]),
        drain_per_s=float(t["drain_per_s"]),
        low_fuel_threshold=float(t["low_fuel_threshold"]),
        score=ScoreTuning(
            per_mote=int(s["per_mote"]),
            per_lantern=int(s["per_lantern"]),
            per_stun=int(s["per_stun"]),
            per_second_left=int(s["per_second_left"]),
            per_flame_left=int(s["per_flame_left"]),
        ),
    )
