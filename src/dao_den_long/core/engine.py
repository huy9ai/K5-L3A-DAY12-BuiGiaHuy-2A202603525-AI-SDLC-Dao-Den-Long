"""Deterministic 60Hz 3-Night simulation engine complying with Test Contract v1.1."""

from __future__ import annotations

from dataclasses import dataclass, field
import math
import random
from typing import Any

from dao_den_long.core.config import (
    CHARM_DURATION_TICKS,
    CHARM_RESPAWN_TICKS,
    CHARM_SPEED,
    DRIFTER_CHASE_SPEED,
    DRIFTER_DETECT_RADIUS,
    DRIFTER_DROP_FLEE_TICKS,
    DRIFTER_FLEE_SPEED,
    DRIFTER_FLEE_TICKS,
    DRIFTER_IDLE_SPEED,
    DRIFTER_MAX,
    DRIFTER_SPAWN_INTERVAL_TICKS,
    DRIFTER_STEAL_MAX,
    DRIFTER_STEAL_MIN_CARRIED,
    DRIFTER_STEAL_RADIUS,
    DROPPED_MOTE_TTL_TICKS,
    DT,
    ENTITY_MAX_HEIGHT_DIFF,
    FALL_Y_THRESHOLD,
    GRAVITY,
    INVULN_TICKS,
    JUMP_VELOCITY,
    MOTE_CAP,
    MOTE_INIT_COUNT,
    MOTE_SPAWN_INTERVAL_TICKS,
    PULSE_CENTER_Y_OFFSET,
    PULSE_PUSH_TICKS,
    RESPAWN_WAIT_TICKS,
    SAFE_PUSHOUT_MAX_TICKS,
    SHADE_DETECT_RADIUS,
    SHADE_LEASH_RADIUS,
    SHADE_RECOIL_DIST,
    SHADE_RECOIL_TICKS,
    SHADE_SPAWN_TICKS,
    SHADE_WANDER_SPEED,
    TICK_RATE,
    WIND_DURATION_TICKS,
    WIND_INTERVAL_TICKS,
    WIND_PUSH_SPEED,
    WIND_WARN_TICKS,
    TuningConfig,
    load_tuning,
)
from dao_den_long.core.maps import MapDefinition, build_night_map


def _r3(value: float) -> float:
    rounded = round(float(value), 3)
    return 0.0 if rounded == 0.0 else rounded


def _xz_dist(ax: float, az: float, bx: float, bz: float) -> float:
    return math.hypot(ax - bx, az - bz)


def _dist3(ax: float, ay: float, az: float, bx: float, by: float, bz: float) -> float:
    return math.sqrt((ax - bx) ** 2 + (ay - by) ** 2 + (az - bz) ** 2)


@dataclass
class InputFrame:
    """Single-tick normalized player control state (Contract v1.1)."""

    move: tuple[float, float] = (0.0, 0.0)
    cam_yaw_deg: float = 0.0
    jump: bool = False
    dash: bool = False
    interact: bool = False
    pulse: bool = False
    pause: bool = False


@dataclass
class PlayerState:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    vx: float = 0.0
    vy: float = 0.0
    vz: float = 0.0
    grounded: bool = True
    carried: int = 0
    flames: int = 3
    invuln_ticks: int = 0
    dash_ticks: int = 0
    dash_cd_ticks: int = 0
    dash_dir_x: float = 0.0
    dash_dir_z: float = 1.0
    pulse_cd_ticks: int = 0
    charm_ticks: int = 0
    respawn_ticks: int = 0
    is_launched: bool = False
    launch_vx: float = 0.0
    launch_vz: float = 0.0
    facing_yaw_deg: float = 0.0


@dataclass
class LanternState:
    id: str
    x: float
    y: float
    z: float
    lit: bool = False
    deposited: int = 0


@dataclass
class ShadeState:
    id: str
    x: float
    y: float
    z: float
    state: str = "chase"
    state_ticks_left: int = 0
    push_ticks_left: int = 0
    push_dir_x: float = 1.0
    push_dir_z: float = 0.0
    recoil_dir_x: float = 1.0
    recoil_dir_z: float = 0.0
    safe_push_ticks: int = 0
    wander_angle: float = 0.0


@dataclass
class MoteState:
    id: str
    x: float
    y: float
    z: float
    kind: str = "random"
    ttl_ticks: int | None = None
    pickup_delay_ticks: int = 0


@dataclass
class DrifterState:
    id: str
    x: float
    y: float
    z: float
    state: str = "idle"
    stolen: int = 0
    has_stolen: bool = False
    flee_ticks_left: int = 0
    orbit_angle: float = 0.0


@dataclass
class CharmState:
    id: str
    x: float
    y: float
    z: float
    available: bool = True
    respawn_ticks: int = 0


@dataclass
class _PrevButtons:
    jump: bool = False
    dash: bool = False
    interact: bool = False
    pulse: bool = False
    pause: bool = False


@dataclass
class GameSimulation:
    """Deterministic 60Hz simulation engine for Nights 1-3 (Contract v1.1)."""

    seed: int = 42
    night: int = 1
    tuning: TuningConfig = field(default_factory=load_tuning)
    scenario: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        self._rng = random.Random(self.seed)
        self.map_def: MapDefinition = build_night_map(self.night)
        self.tick = 0
        self.sim_tick = 0
        self.state = "playing"
        self.score = 0
        self._night_started = False
        self._prev_buttons = _PrevButtons()
        self._seq = {"M": 0, "S": 0, "D": 0}

        sc = self.scenario or {}
        self.random_motes = bool(sc.get("random_motes", True))
        self.random_shades = bool(sc.get("random_shades", True))
        self.random_drifters = bool(sc.get("random_drifters", self.map_def.has_drifters))
        self.wind_enabled = bool(sc.get("wind_enabled", self.map_def.has_wind))

        default_dur = (
            self.tuning.night1_duration_s
            if self.night == 1
            else (self.tuning.night2_duration_s if self.night == 2 else self.tuning.night3_duration_s)
        )
        self.initial_time_left_s = float(sc.get("time_left_s", default_dur))
        self.time_left_s = self.initial_time_left_s

        # Wind state (Night 3)
        self.wind_active = False
        self.wind_warning = False
        self.wind_dir_deg = 0.0
        self.wind_ticks_left = 0

        # Player setup
        p_cfg = sc.get("player", {})
        p_pos = p_cfg.get("pos", list(self.map_def.player_spawn))
        px, py, pz = float(p_pos[0]), float(p_pos[1]), float(p_pos[2])
        ground_y = self.map_def.ground_height(px, pz)
        grounded = ground_y is not None and abs(py - ground_y) <= 0.05
        self.player = PlayerState(
            x=px,
            y=py,
            z=pz,
            grounded=grounded,
            carried=int(p_cfg.get("carried", 0)),
            flames=int(p_cfg.get("flames", self.tuning.flames)),
            invuln_ticks=int(p_cfg.get("invuln_ticks", 0)),
            dash_cd_ticks=int(p_cfg.get("dash_cd_ticks", 0)),
            pulse_cd_ticks=int(p_cfg.get("pulse_cd_ticks", 0)),
            charm_ticks=int(p_cfg.get("charm_ticks", 0)),
        )

        # Lanterns
        self.lanterns: list[LanternState] = [
            LanternState(id=lid, x=pos[0], y=pos[1], z=pos[2])
            for lid, pos in self.map_def.lantern_spawns
        ]
        lantern_by_id = {l.id: l for l in self.lanterns}
        for l_cfg in sc.get("lanterns", []):
            lid = str(l_cfg["id"])
            if lid in lantern_by_id:
                target = lantern_by_id[lid]
                if "pos" in l_cfg:
                    pos = l_cfg["pos"]
                    target.x, target.y, target.z = float(pos[0]), float(pos[1]), float(pos[2])
                if "deposited" in l_cfg:
                    target.deposited = int(l_cfg["deposited"])
                if "lit" in l_cfg:
                    target.lit = bool(l_cfg["lit"])
                    if target.lit and "deposited" not in l_cfg:
                        target.deposited = self.tuning.lantern_cost
                elif target.deposited >= self.tuning.lantern_cost:
                    target.lit = True

        # Motes (20 at 20 distinct points initially if random_motes=True)
        self.motes: list[MoteState] = []
        if "motes" in sc:
            used_m = {str(it["id"]) for it in sc["motes"] if isinstance(it, dict) and it.get("id") is not None}
            for item in sc["motes"]:
                if isinstance(item, dict):
                    pos = item["pos"]
                    mid = str(item["id"]) if item.get("id") is not None else self._next_id("M", used_m)
                    used_m.add(mid)
                    kind = str(item.get("kind", "random"))
                    ttl_raw = item.get("ttl_s")
                    ttl_t = round(float(ttl_raw) * TICK_RATE) if ttl_raw is not None else (
                        DROPPED_MOTE_TTL_TICKS if kind == "dropped" else None
                    )
                else:
                    pos = item
                    mid = self._next_id("M", used_m)
                    used_m.add(mid)
                    kind = "random"
                    ttl_t = None
                self.motes.append(
                    MoteState(id=mid, x=float(pos[0]), y=float(pos[1]), z=float(pos[2]), kind=kind, ttl_ticks=ttl_t)
                )
        elif self.random_motes:
            points = list(self.map_def.mote_spawns)
            self._rng.shuffle(points)
            for pt in points[: min(MOTE_INIT_COUNT, len(points))]:
                self.motes.append(MoteState(id=self._next_id("M"), x=pt[0], y=pt[1], z=pt[2], kind="random"))

        # Shades (start empty if random_shades=True; 2 spawn at tick 300)
        self.shades: list[ShadeState] = []
        if "shades" in sc:
            used_s = {str(it["id"]) for it in sc["shades"] if isinstance(it, dict) and it.get("id") is not None}
            for item in sc["shades"]:
                if isinstance(item, dict):
                    pos = item["pos"]
                    sid = str(item["id"]) if item.get("id") is not None else self._next_id("S", used_s)
                    used_s.add(sid)
                    s_state = str(item.get("state", "chase"))
                    s_ticks = int(item.get("state_ticks_left", 0))
                else:
                    pos = item
                    sid = self._next_id("S", used_s)
                    used_s.add(sid)
                    s_state = "chase"
                    s_ticks = 0
                self.shades.append(
                    ShadeState(
                        id=sid,
                        x=float(pos[0]),
                        y=float(pos[1]),
                        z=float(pos[2]),
                        state=s_state,
                        state_ticks_left=s_ticks,
                        wander_angle=self._rng.uniform(0.0, 2.0 * math.pi),
                    )
                )

        # Drifters (Gió Lạc)
        self.drifters: list[DrifterState] = []
        if "drifters" in sc:
            used_d = {str(it["id"]) for it in sc["drifters"] if isinstance(it, dict) and it.get("id") is not None}
            for item in sc["drifters"]:
                if isinstance(item, dict):
                    pos = item["pos"]
                    did = str(item["id"]) if item.get("id") is not None else self._next_id("D", used_d)
                    used_d.add(did)
                    d_state = str(item.get("state", "idle"))
                    stolen = int(item.get("stolen", 0))
                    flee_left = int(item.get("flee_ticks_left", DRIFTER_FLEE_TICKS if d_state == "flee" else 0))
                else:
                    pos = item
                    did = self._next_id("D", used_d)
                    used_d.add(did)
                    d_state = "idle"
                    stolen = 0
                    flee_left = 0
                self.drifters.append(
                    DrifterState(
                        id=did,
                        x=float(pos[0]),
                        y=float(pos[1]),
                        z=float(pos[2]),
                        state=d_state,
                        stolen=stolen,
                        has_stolen=stolen > 0,
                        flee_ticks_left=flee_left,
                        orbit_angle=self._rng.uniform(0.0, 2.0 * math.pi),
                    )
                )

        # Charms (Bùa Gió)
        self.charms: list[CharmState] = []
        if "charms" in sc:
            for idx, item in enumerate(sc["charms"]):
                cid = str(item.get("id") or f"C{idx + 1}")
                pos = item.get("pos", [0.0, 0.0, 0.0])
                avail = bool(item.get("available", True))
                resp = int(item.get("respawn_ticks", 0 if avail else CHARM_RESPAWN_TICKS))
                self.charms.append(
                    CharmState(id=cid, x=float(pos[0]), y=float(pos[1]), z=float(pos[2]), available=avail, respawn_ticks=resp)
                )
        else:
            for cid, pos in self.map_def.charm_spawns:
                self.charms.append(CharmState(id=cid, x=pos[0], y=pos[1], z=pos[2]))

    def _next_id(self, prefix: str, used_ids: set[str] | None = None) -> str:
        if used_ids is not None:
            existing = used_ids
        elif prefix == "M":
            existing = {m.id for m in self.motes}
        elif prefix == "S":
            existing = {s.id for s in self.shades}
        else:
            existing = {d.id for d in self.drifters}

        while True:
            self._seq[prefix] += 1
            cand = f"{prefix}{self._seq[prefix]}"
            if cand not in existing:
                return cand

    def _is_point_occupied_for_mote(self, pt: tuple[float, float, float]) -> bool:
        return any(
            _xz_dist(m.x, m.z, pt[0], pt[2]) <= 0.5 and abs(m.y - pt[1]) <= 1.0
            for m in self.motes
        )

    def _pick_free_shade_point(self) -> tuple[float, float, float] | None:
        candidates = [
            pt
            for pt in self.map_def.shade_spawns
            if _xz_dist(pt[0], pt[2], self.player.x, self.player.z) >= 15.0 - 1e-9
            and all(_xz_dist(pt[0], pt[2], l.x, l.z) >= self.tuning.safe_radius for l in self.lanterns if l.lit)
        ]
        if not candidates:
            return None
        return self._rng.choice(candidates)

    def _move_shade_step(self, shade: ShadeState, dx: float, dz: float) -> bool:
        """Move shade horizontally respecting terrain, obstacles, void, and safe_radius."""
        nx, nz, blocked = self.map_def.resolve_horizontal_move(
            shade.x, shade.y, shade.z, shade.x + dx, shade.z + dz, allow_void=False
        )
        # Do not allow shades outside safe_radius to enter lit lanterns' safe_radius
        if shade.safe_push_ticks == 0:
            for l in self.lanterns:
                if l.lit and _xz_dist(nx, nz, l.x, l.z) < self.tuning.safe_radius + 0.002:
                    dist = _xz_dist(nx, nz, l.x, l.z)
                    if dist > 1e-9:
                        ux = (nx - l.x) / dist
                        uz = (nz - l.z) / dist
                    else:
                        ux, uz = 1.0, 0.0
                    cand_x = l.x + ux * (self.tuning.safe_radius + 0.002)
                    cand_z = l.z + uz * (self.tuning.safe_radius + 0.002)
                    if self.map_def.ground_height(cand_x, cand_z) is not None and not self.map_def.is_blocked_obstacle(cand_x, shade.y, cand_z):
                        nx, nz = cand_x, cand_z
                    else:
                        nx, nz = shade.x, shade.z
                    blocked = True
        shade.x = nx
        shade.z = nz
        gy = self.map_def.ground_height(shade.x, shade.z)
        if gy is not None:
            shade.y = gy
        return blocked

    def _update_safe_radius(self) -> None:
        min_r = self.tuning.safe_radius + 0.002
        for shade in self.shades:
            inside_lit = None
            for l in self.lanterns:
                if l.lit and _xz_dist(shade.x, shade.z, l.x, l.z) < self.tuning.safe_radius - 1e-6:
                    inside_lit = l
                    break

            if inside_lit is not None:
                if shade.safe_push_ticks <= 0:
                    shade.safe_push_ticks = SAFE_PUSHOUT_MAX_TICKS
                dx = shade.x - inside_lit.x
                dz = shade.z - inside_lit.z
                dist = math.hypot(dx, dz)
                if dist > 1e-9:
                    ux, uz = dx / dist, dz / dist
                else:
                    ux, uz = 1.0, 0.0
                remaining_dist = max(0.0, min_r - dist)
                step_dist = remaining_dist / max(1, shade.safe_push_ticks)
                nx, nz, _ = self.map_def.resolve_horizontal_move(
                    shade.x, shade.y, shade.z, shade.x + ux * step_dist, shade.z + uz * step_dist, allow_void=False
                )
                shade.x, shade.z = nx, nz
                gy = self.map_def.ground_height(shade.x, shade.z)
                if gy is not None:
                    shade.y = gy
                if _xz_dist(shade.x, shade.z, inside_lit.x, inside_lit.z) >= self.tuning.safe_radius:
                    shade.safe_push_ticks = 0
            else:
                shade.safe_push_ticks = 0

    def step(self, inputs: InputFrame | None = None) -> list[dict[str, Any]]:
        """Execute 1 tick following Ticket-02 mandatory 12-step order."""
        if self.state in ("won", "lost"):
            return []

        inp = inputs or InputFrame()
        self.tick += 1
        events: list[dict[str, Any]] = []

        # === Step 1: Read input & process pause first ===
        pause_edge = inp.pause and not self._prev_buttons.pause
        jump_edge = inp.jump and not self._prev_buttons.jump
        dash_edge = inp.dash and not self._prev_buttons.dash
        interact_edge = inp.interact and not self._prev_buttons.interact
        pulse_edge = inp.pulse and not self._prev_buttons.pulse
        self._prev_buttons = _PrevButtons(
            jump=inp.jump,
            dash=inp.dash,
            interact=inp.interact,
            pulse=inp.pulse,
            pause=inp.pause,
        )

        if pause_edge:
            if self.state == "playing":
                self.state = "paused"
                events.append({"type": "event", "tick": self.tick, "name": "paused", "data": {}})
                return events
            if self.state == "paused":
                self.state = "playing"
                events.append({"type": "event", "tick": self.tick, "name": "resumed", "data": {}})

        if self.state == "paused":
            return events

        # Emit night_start on first active tick
        if not self._night_started:
            self._night_started = True
            events.append({"type": "event", "tick": self.tick, "name": "night_start", "data": {"night": self.night}})

        # === Step 2: Decrement counters ===
        self.sim_tick += 1
        self.time_left_s = max(0.0, self.initial_time_left_s - (self.sim_tick / TICK_RATE))

        if self.player.invuln_ticks > 0:
            self.player.invuln_ticks -= 1
        if self.player.charm_ticks > 0:
            self.player.charm_ticks -= 1
        if self.player.charm_ticks > 0:
            self.player.dash_cd_ticks = 0
        elif self.player.dash_cd_ticks > 0:
            self.player.dash_cd_ticks -= 1
        if self.player.pulse_cd_ticks > 0:
            self.player.pulse_cd_ticks -= 1

        if self.player.respawn_ticks > 0:
            self.player.respawn_ticks -= 1
            if self.player.respawn_ticks == 0:
                sx, sy, sz = self.map_def.player_spawn
                self.player.x, self.player.y, self.player.z = sx, sy, sz
                self.player.vx = self.player.vy = self.player.vz = 0.0
                self.player.grounded = True
                self.player.is_launched = False
                self.player.invuln_ticks = INVULN_TICKS

        for shade in self.shades:
            if shade.safe_push_ticks > 0:
                shade.safe_push_ticks -= 1
            if shade.state in ("spawning", "recoil", "stunned") and shade.state_ticks_left > 0:
                shade.state_ticks_left -= 1
                if shade.state_ticks_left == 0:
                    dist_p = _xz_dist(self.player.x, self.player.z, shade.x, shade.z)
                    shade.state = "chase" if (self.player.respawn_ticks == 0 and dist_p <= SHADE_DETECT_RADIUS) else "wander"

        kept_drifters: list[DrifterState] = []
        for d in self.drifters:
            if d.state == "flee" and d.flee_ticks_left > 0:
                d.flee_ticks_left -= 1
                if d.flee_ticks_left == 0:
                    continue
            kept_drifters.append(d)
        self.drifters = kept_drifters

        kept_motes: list[MoteState] = []
        for m in self.motes:
            if m.pickup_delay_ticks > 0:
                m.pickup_delay_ticks -= 1
            if m.ttl_ticks is not None:
                m.ttl_ticks -= 1
                if m.ttl_ticks <= 0:
                    continue
            kept_motes.append(m)
        self.motes = kept_motes

        for charm in self.charms:
            if not charm.available and charm.respawn_ticks > 0:
                charm.respawn_ticks -= 1
                if charm.respawn_ticks == 0:
                    charm.available = True

        # Night 3 wind timer
        if self.wind_enabled:
            if self.wind_active:
                self.wind_ticks_left -= 1
                if self.wind_ticks_left <= 0:
                    self.wind_active = False
            else:
                mod = self.sim_tick % WIND_INTERVAL_TICKS
                if mod == WIND_INTERVAL_TICKS - WIND_WARN_TICKS:
                    self.wind_warning = True
                    self.wind_dir_deg = round(self._rng.uniform(0.0, 360.0), 1)
                elif self.sim_tick > 0 and mod == 0:
                    self.wind_warning = False
                    self.wind_active = True
                    self.wind_ticks_left = WIND_DURATION_TICKS

        # === Step 3: Move May (jump, dash, pads, wind) & check fall ===
        if self.player.respawn_ticks == 0:
            mx, mz = float(inp.move[0]), float(inp.move[1])
            mag = math.hypot(mx, mz)
            if mag > 1.0:
                mx /= mag
                mz /= mag
            theta = math.radians(float(inp.cam_yaw_deg))
            wx = mx * math.cos(theta) + mz * math.sin(theta)
            wz = -mx * math.sin(theta) + mz * math.cos(theta)
            wmag = math.hypot(wx, wz)
            if wmag > 1e-6:
                self.player.facing_yaw_deg = math.degrees(math.atan2(wx, wz))

            # Dash trigger (rising edge; ignored if already dashing)
            if dash_edge and self.player.dash_ticks == 0 and (
                self.player.dash_cd_ticks == 0 or self.player.charm_ticks > 0
            ):
                if wmag > 1e-6:
                    dx, dz = wx / wmag, wz / wmag
                else:
                    frad = math.radians(self.player.facing_yaw_deg)
                    dx, dz = math.sin(frad), math.cos(frad)
                self.player.dash_ticks = round(self.tuning.dash_duration_s * TICK_RATE)
                self.player.dash_dir_x = dx
                self.player.dash_dir_z = dz
                self.player.dash_cd_ticks = 0 if self.player.charm_ticks > 0 else round(self.tuning.dash_cooldown_s * TICK_RATE)
                self.player.is_launched = False
                self.player.vy = 0.0
                events.append({"type": "event", "tick": self.tick, "name": "dash", "data": {}})

            if self.player.dash_ticks > 0:
                vx = self.player.dash_dir_x * self.tuning.dash_speed
                vz = self.player.dash_dir_z * self.tuning.dash_speed
                self.player.dash_ticks -= 1
                self.player.vy = 0.0
                dashing_now = True
            elif self.player.is_launched:
                vx = self.player.launch_vx
                vz = self.player.launch_vz
                dashing_now = False
            else:
                spd = CHARM_SPEED if self.player.charm_ticks > 0 else self.tuning.player_speed
                vx = wx * spd
                vz = wz * spd
                dashing_now = False

            if self.wind_active:
                wrad = math.radians(self.wind_dir_deg)
                vx += math.cos(wrad) * WIND_PUSH_SPEED
                vz += math.sin(wrad) * WIND_PUSH_SPEED

            nx, nz, _ = self.map_def.resolve_horizontal_move(
                self.player.x, self.player.y, self.player.z,
                self.player.x + vx * DT, self.player.z + vz * DT,
                allow_void=True,
            )
            self.player.x = nx
            self.player.z = nz

            if jump_edge and self.player.grounded and not dashing_now:
                self.player.vy = JUMP_VELOCITY
                self.player.grounded = False

            if not dashing_now:
                prev_y = self.player.y
                ground_y = self.map_def.ground_height(self.player.x, self.player.z)
                if self.player.grounded:
                    if ground_y is None or ground_y < self.player.y - 0.55:
                        self.player.grounded = False
                    else:
                        self.player.y = ground_y
                        self.player.vy = 0.0
                if not self.player.grounded:
                    self.player.y += self.player.vy * DT
                    self.player.vy -= GRAVITY * DT
                    ground_y = self.map_def.ground_height(self.player.x, self.player.z)
                    if (
                        ground_y is not None
                        and self.player.vy <= 0.0
                        and prev_y >= ground_y - 0.55
                        and self.player.y <= ground_y
                    ):
                        self.player.y = ground_y
                        self.player.vy = 0.0
                        self.player.grounded = True
                        self.player.is_launched = False

                # Launch pads check on grounded
                if self.player.grounded:
                    for pad in self.map_def.launch_pads:
                        if _xz_dist(self.player.x, self.player.z, pad.x, pad.z) <= pad.radius + 1e-9 and abs(self.player.y - pad.y) <= 0.5:
                            self.player.vy = pad.vy
                            self.player.launch_vx = pad.vx
                            self.player.launch_vz = pad.vz
                            self.player.is_launched = True
                            self.player.grounded = False
                            vx, vz = pad.vx, pad.vz
                            break

            self.player.vx = vx
            self.player.vz = vz

            # Fall check (Y < -10)
            if self.tuning.fall_enabled and self.player.y < FALL_Y_THRESHOLD:
                lost = self.player.carried
                self.player.carried = 0
                self.player.flames = max(0, self.player.flames - 1)
                self.player.vx = self.player.vy = self.player.vz = 0.0
                self.player.dash_ticks = 0
                self.player.is_launched = False
                events.append(
                    {
                        "type": "event",
                        "tick": self.tick,
                        "name": "player_hit",
                        "data": {"by": "fall", "flames": self.player.flames, "dropped": 0, "lost": lost},
                    }
                )
                if self.player.flames > 0:
                    self.player.respawn_ticks = RESPAWN_WAIT_TICKS

        # === Step 4: Pickup motes and charms ===
        if self.player.respawn_ticks == 0:
            rem_motes: list[MoteState] = []
            for m in self.motes:
                if (
                    m.pickup_delay_ticks == 0
                    and self.player.carried < self.tuning.carry_capacity
                    and _xz_dist(self.player.x, self.player.z, m.x, m.z) <= self.tuning.pickup_radius + 1e-9
                    and abs(self.player.y - m.y) <= ENTITY_MAX_HEIGHT_DIFF + 1e-9
                ):
                    self.player.carried += 1
                    events.append(
                        {"type": "event", "tick": self.tick, "name": "mote_picked", "data": {"carried": self.player.carried}}
                    )
                else:
                    rem_motes.append(m)
            self.motes = rem_motes

            for c in self.charms:
                if (
                    c.available
                    and _xz_dist(self.player.x, self.player.z, c.x, c.z) <= self.tuning.pickup_radius + 1e-9
                    and abs(self.player.y - c.y) <= ENTITY_MAX_HEIGHT_DIFF + 1e-9
                ):
                    c.available = False
                    c.respawn_ticks = CHARM_RESPAWN_TICKS
                    self.player.charm_ticks = CHARM_DURATION_TICKS
                    self.player.dash_cd_ticks = 0
                    events.append(
                        {
                            "type": "event",
                            "tick": self.tick,
                            "name": "charm_picked",
                            "data": {"charm_id": c.id, "charm_ticks": CHARM_DURATION_TICKS},
                        }
                    )

        # === Step 5: Interact with lanterns ===
        if self.player.respawn_ticks == 0 and interact_edge and self.player.carried > 0:
            candidates = [
                (_xz_dist(self.player.x, self.player.z, l.x, l.z), l.id, l)
                for l in self.lanterns
                if not l.lit and _xz_dist(self.player.x, self.player.z, l.x, l.z) <= self.tuning.interact_radius + 1e-9
            ]
            if candidates:
                candidates.sort(key=lambda it: (it[0], it[1]))
                target = candidates[0][2]
                amount = min(self.player.carried, max(0, self.tuning.lantern_cost - target.deposited))
                if amount > 0:
                    self.player.carried -= amount
                    target.deposited += amount
                    self.score += amount * self.tuning.score.per_mote
                    events.append(
                        {
                            "type": "event",
                            "tick": self.tick,
                            "name": "deposit",
                            "data": {"lantern_id": target.id, "amount": amount, "deposited": target.deposited},
                        }
                    )
                    if target.deposited >= self.tuning.lantern_cost:
                        target.lit = True
                        self.score += self.tuning.score.per_lantern
                        events.append(
                            {
                                "type": "event",
                                "tick": self.tick,
                                "name": "lantern_lit",
                                "data": {"lantern_id": target.id},
                            }
                        )
                        for s in self.shades:
                            if _xz_dist(s.x, s.z, target.x, target.z) < self.tuning.safe_radius:
                                s.safe_push_ticks = SAFE_PUSHOUT_MAX_TICKS

        # === Step 6: Update safe radius ===
        self._update_safe_radius()

        # === Step 7: Pulse (Tỏa Sáng) ===
        if (
            self.player.respawn_ticks == 0
            and pulse_edge
            and self.player.carried >= self.tuning.pulse_cost
            and self.player.pulse_cd_ticks <= 0
        ):
            self.player.carried -= self.tuning.pulse_cost
            self.player.pulse_cd_ticks = round(self.tuning.pulse_cooldown_s * TICK_RATE)
            cx, cy, cz = self.player.x, self.player.y + PULSE_CENTER_Y_OFFSET, self.player.z
            stunned_ids: list[str] = []
            stun_ticks = round(self.tuning.pulse_stun_s * TICK_RATE)
            for s in sorted(self.shades, key=lambda it: it.id):
                if _dist3(cx, cy, cz, s.x, s.y, s.z) <= self.tuning.pulse_radius + 1e-9:
                    s.state = "stunned"
                    s.state_ticks_left = stun_ticks
                    s.push_ticks_left = PULSE_PUSH_TICKS
                    dx = s.x - self.player.x
                    dz = s.z - self.player.z
                    hdist = math.hypot(dx, dz)
                    if hdist > 1e-9:
                        s.push_dir_x, s.push_dir_z = dx / hdist, dz / hdist
                    else:
                        s.push_dir_x, s.push_dir_z = 1.0, 0.0
                    self.score += self.tuning.score.per_stun
                    stunned_ids.append(s.id)

            for d in sorted(self.drifters, key=lambda it: it.id):
                if _dist3(cx, cy, cz, d.x, d.y, d.z) <= self.tuning.pulse_radius + 1e-9:
                    if d.state == "chase":
                        d.state = "flee"
                        d.flee_ticks_left = DRIFTER_FLEE_TICKS
                    elif d.state == "flee" and d.stolen > 0:
                        amt = d.stolen
                        gy = self.map_def.ground_height(d.x, d.z)
                        drop_y = gy if gy is not None else max(0.0, d.y)
                        for idx in range(amt):
                            ang = (2.0 * math.pi * idx) / amt
                            mx_d = d.x + 0.5 * math.cos(ang)
                            mz_d = d.z + 0.5 * math.sin(ang)
                            mgy = self.map_def.ground_height(mx_d, mz_d)
                            if mgy is None:
                                mx_d, mz_d, mgy = d.x, d.z, drop_y
                            self.motes.append(
                                MoteState(
                                    id=self._next_id("M"),
                                    x=mx_d,
                                    y=mgy,
                                    z=mz_d,
                                    kind="dropped",
                                    ttl_ticks=DROPPED_MOTE_TTL_TICKS,
                                    pickup_delay_ticks=1,
                                )
                            )
                        events.append(
                            {
                                "type": "event",
                                "tick": self.tick,
                                "name": "drifter_drop",
                                "data": {"drifter_id": d.id, "amount": amt},
                            }
                        )
                        d.stolen = 0
                        d.flee_ticks_left = DRIFTER_DROP_FLEE_TICKS

            events.append({"type": "event", "tick": self.tick, "name": "pulse", "data": {"stunned_ids": stunned_ids}})

        # === Step 8: Move Shades & Drifters ===
        for s in self.shades:
            if s.state == "spawning":
                continue
            if s.state == "stunned":
                if s.push_ticks_left > 0:
                    step_m = self.tuning.pulse_push_m / PULSE_PUSH_TICKS
                    blocked = self._move_shade_step(s, s.push_dir_x * step_m, s.push_dir_z * step_m)
                    s.push_ticks_left -= 1
                    if blocked:
                        s.push_ticks_left = 0
                continue
            if s.state == "recoil":
                step_m = SHADE_RECOIL_DIST / SHADE_RECOIL_TICKS
                self._move_shade_step(s, s.recoil_dir_x * step_m, s.recoil_dir_z * step_m)
                continue

            dist_p = _xz_dist(self.player.x, self.player.z, s.x, s.z)
            if s.state == "wander":
                if self.player.respawn_ticks == 0 and dist_p <= SHADE_DETECT_RADIUS + 1e-9:
                    s.state = "chase"
                else:
                    s.wander_angle += 0.4 * DT
                    blocked = self._move_shade_step(
                        s,
                        math.cos(s.wander_angle) * SHADE_WANDER_SPEED * DT,
                        math.sin(s.wander_angle) * SHADE_WANDER_SPEED * DT,
                    )
                    if blocked:
                        s.wander_angle += math.pi * 0.75
                    continue

            if s.state == "chase":
                if self.player.respawn_ticks > 0 or dist_p > SHADE_LEASH_RADIUS + 1e-9:
                    s.state = "wander"
                    continue
                dx = self.player.x - s.x
                dz = self.player.z - s.z
                if dist_p > 1e-9:
                    step_m = min(dist_p, self.map_def.shade_speed * DT)
                    self._move_shade_step(s, (dx / dist_p) * step_m, (dz / dist_p) * step_m)

        for d in self.drifters:
            dist_p = _xz_dist(self.player.x, self.player.z, d.x, d.z)
            if d.state == "idle":
                if self.player.respawn_ticks == 0 and self.player.carried >= DRIFTER_STEAL_MIN_CARRIED and dist_p <= DRIFTER_DETECT_RADIUS + 1e-9:
                    d.state = "chase"
                else:
                    d.orbit_angle += 0.6 * DT
                    d.x += math.cos(d.orbit_angle) * DRIFTER_IDLE_SPEED * DT
                    d.z += math.sin(d.orbit_angle) * DRIFTER_IDLE_SPEED * DT
                    continue
            if d.state == "chase":
                if self.player.respawn_ticks > 0 or self.player.carried < DRIFTER_STEAL_MIN_CARRIED or dist_p > DRIFTER_DETECT_RADIUS + 1e-9:
                    d.state = "idle"
                elif dist_p > 1e-9:
                    step_m = min(dist_p, DRIFTER_CHASE_SPEED * DT)
                    d.x += ((self.player.x - d.x) / dist_p) * step_m
                    d.z += ((self.player.z - d.z) / dist_p) * step_m
            elif d.state == "flee":
                dx = d.x - self.player.x
                dz = d.z - self.player.z
                hdist = math.hypot(dx, dz)
                ux, uz = (dx / hdist, dz / hdist) if hdist > 1e-9 else (1.0, 0.0)
                d.x += ux * DRIFTER_FLEE_SPEED * DT
                d.z += uz * DRIFTER_FLEE_SPEED * DT

        # === Step 9: Collisions — Drifters steal first, then Shades hit (sorted by id) ===
        if self.player.respawn_ticks == 0:
            for d in sorted(self.drifters, key=lambda it: it.id):
                if (
                    d.state == "chase"
                    and not d.has_stolen
                    and self.player.carried > 0
                    and _xz_dist(self.player.x, self.player.z, d.x, d.z) <= DRIFTER_STEAL_RADIUS + 1e-9
                ):
                    amt = min(DRIFTER_STEAL_MAX, self.player.carried)
                    self.player.carried -= amt
                    d.stolen = amt
                    d.has_stolen = True
                    d.state = "flee"
                    d.flee_ticks_left = DRIFTER_FLEE_TICKS
                    events.append(
                        {
                            "type": "event",
                            "tick": self.tick,
                            "name": "drifter_steal",
                            "data": {"drifter_id": d.id, "amount": amt, "carried": self.player.carried},
                        }
                    )

            if self.player.invuln_ticks == 0:
                for s in sorted(self.shades, key=lambda it: it.id):
                    if s.state not in ("wander", "chase") or s.safe_push_ticks > 0:
                        continue
                    if any(l.lit and _xz_dist(s.x, s.z, l.x, l.z) < self.tuning.safe_radius - 1e-6 for l in self.lanterns):
                        continue
                    if (
                        _xz_dist(self.player.x, self.player.z, s.x, s.z) <= self.tuning.shade_hit_radius + 1e-9
                        and abs(self.player.y - s.y) <= ENTITY_MAX_HEIGHT_DIFF + 1e-9
                    ):
                        self.player.flames = max(0, self.player.flames - 1)
                        dropped = int(math.floor(self.player.carried * self.tuning.hit_drop_ratio + 1e-9))
                        self.player.carried -= dropped
                        self.player.invuln_ticks = INVULN_TICKS
                        for idx in range(dropped):
                            ang = self._rng.uniform(0.0, 2.0 * math.pi)
                            rad = self._rng.uniform(1.5, 2.5)
                            mx_d = self.player.x + rad * math.cos(ang)
                            mz_d = self.player.z + rad * math.sin(ang)
                            mgy = self.map_def.ground_height(mx_d, mz_d)
                            if mgy is None:
                                mx_d, mz_d = self.player.x, self.player.z
                                mgy = max(0.0, self.player.y)
                            self.motes.append(
                                MoteState(
                                    id=self._next_id("M"),
                                    x=mx_d,
                                    y=mgy,
                                    z=mz_d,
                                    kind="dropped",
                                    ttl_ticks=DROPPED_MOTE_TTL_TICKS,
                                    pickup_delay_ticks=1,
                                )
                            )
                        dx = s.x - self.player.x
                        dz = s.z - self.player.z
                        hdist = math.hypot(dx, dz)
                        s.recoil_dir_x, s.recoil_dir_z = (dx / hdist, dz / hdist) if hdist > 1e-9 else (1.0, 0.0)
                        s.state = "recoil"
                        s.state_ticks_left = SHADE_RECOIL_TICKS
                        events.append(
                            {
                                "type": "event",
                                "tick": self.tick,
                                "name": "player_hit",
                                "data": {"by": "shade", "flames": self.player.flames, "dropped": dropped},
                            }
                        )
                        break

        # === Step 10: Scheduled spawns (new entities interactive from next tick) ===
        if self.random_motes and self.sim_tick % MOTE_SPAWN_INTERVAL_TICKS == 0 and len(self.motes) < MOTE_CAP:
            free_pts = [pt for pt in self.map_def.mote_spawns if not self._is_point_occupied_for_mote(pt)]
            if free_pts:
                pt = self._rng.choice(free_pts)
                self.motes.append(MoteState(id=self._next_id("M"), x=pt[0], y=pt[1], z=pt[2], kind="random"))

        if self.random_shades and len(self.shades) < self.map_def.max_shades:
            spawn_count = 0
            if self.sim_tick == 300:
                spawn_count = min(2, self.map_def.max_shades - len(self.shades))
            elif self.sim_tick > 300 and (self.sim_tick - 300) % self.map_def.shade_spawn_interval == 0:
                spawn_count = 1
            for _ in range(spawn_count):
                pt = self._pick_free_shade_point()
                if pt is None:
                    break
                shade = ShadeState(
                    id=self._next_id("S"),
                    x=pt[0],
                    y=pt[1],
                    z=pt[2],
                    state="spawning",
                    state_ticks_left=SHADE_SPAWN_TICKS,
                    wander_angle=self._rng.uniform(0.0, 2.0 * math.pi),
                )
                self.shades.append(shade)
                events.append({"type": "event", "tick": self.tick, "name": "shade_spawned", "data": {"id": shade.id}})

        if (
            self.random_drifters
            and self.map_def.has_drifters
            and self.sim_tick % DRIFTER_SPAWN_INTERVAL_TICKS == 0
            and len(self.drifters) < DRIFTER_MAX
        ):
            pt = self._rng.choice(self.map_def.shade_spawns)
            self.drifters.append(
                DrifterState(
                    id=self._next_id("D"),
                    x=pt[0],
                    y=pt[1] + 1.2,
                    z=pt[2],
                    state="idle",
                    orbit_angle=self._rng.uniform(0.0, 2.0 * math.pi),
                )
            )

        # === Step 11: Win / Loss evaluation (strict priority) ===
        if self.player.flames <= 0:
            self.state = "lost"
            events.append({"type": "event", "tick": self.tick, "name": "game_over", "data": {"result": "lost", "reason": "no_flames"}})
        elif all(l.lit for l in self.lanterns):
            secs_left = int(math.floor(round(self.time_left_s, 6)))
            self.score += secs_left * self.tuning.score.per_second_left + self.player.flames * self.tuning.score.per_flame_left
            self.state = "won"
            events.append({"type": "event", "tick": self.tick, "name": "game_over", "data": {"result": "won", "reason": "all_lit"}})
        elif self.time_left_s <= 1e-9:
            self.time_left_s = 0.0
            self.state = "lost"
            events.append({"type": "event", "tick": self.tick, "name": "game_over", "data": {"result": "lost", "reason": "dawn"}})

        return events

    def snapshot(self) -> dict[str, Any]:
        """Return Test Contract v1.1 snapshot record."""
        return {
            "type": "snapshot",
            "tick": self.tick,
            "sim_tick": self.sim_tick,
            "night": self.night,
            "state": self.state,
            "time_left_s": _r3(self.time_left_s),
            "score": self.score,
            "wind": {
                "active": self.wind_active,
                "dir_deg": _r3(self.wind_dir_deg),
            },
            "player": {
                "pos": [_r3(self.player.x), _r3(self.player.y), _r3(self.player.z)],
                "vel": [_r3(self.player.vx), _r3(self.player.vy), _r3(self.player.vz)],
                "grounded": self.player.grounded,
                "invuln": self.player.invuln_ticks > 0,
                "flames": self.player.flames,
                "carried": self.player.carried,
                "dash_cd_s": _r3(self.player.dash_cd_ticks / TICK_RATE),
                "pulse_cd_s": _r3(self.player.pulse_cd_ticks / TICK_RATE),
                "charm_s": _r3(self.player.charm_ticks / TICK_RATE),
            },
            "lanterns": [
                {
                    "id": l.id,
                    "pos": [_r3(l.x), _r3(l.y), _r3(l.z)],
                    "lit": l.lit,
                    "deposited": l.deposited,
                }
                for l in self.lanterns
            ],
            "shades": [
                {
                    "id": s.id,
                    "pos": [_r3(s.x), _r3(s.y), _r3(s.z)],
                    "state": s.state,
                }
                for s in self.shades
            ],
            "motes_active": len(self.motes),
            "motes": [
                {
                    "id": m.id,
                    "pos": [_r3(m.x), _r3(m.y), _r3(m.z)],
                    "kind": m.kind,
                    "ttl_s": _r3(m.ttl_ticks / TICK_RATE) if m.ttl_ticks is not None else None,
                }
                for m in self.motes
            ],
            "drifters": [
                {
                    "id": d.id,
                    "pos": [_r3(d.x), _r3(d.y), _r3(d.z)],
                    "state": d.state,
                    "stolen": d.stolen,
                }
                for d in self.drifters
            ],
            "charms": [
                {
                    "id": c.id,
                    "available": c.available,
                    "respawn_s": _r3(c.respawn_ticks / TICK_RATE),
                }
                for c in self.charms
            ],
        }

    def end_record(self) -> dict[str, Any]:
        """Return mandatory final JSONL end line."""
        return {
            "type": "end",
            "ticks": self.sim_tick,
            "state": self.state,
            "score": self.score,
        }


class Night1Simulation(GameSimulation):
    """Compatibility alias defaulting to night=1."""

    def __init__(
        self,
        seed: int = 42,
        tuning: TuningConfig | None = None,
        scenario: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            seed=seed,
            night=1,
            tuning=tuning or load_tuning(),
            scenario=scenario,
        )
