"""Deterministic 60Hz Night 1 simulation engine for Dao Den Long (Phase 1 / PRD-0)."""

from __future__ import annotations

from dataclasses import dataclass, field
import math
import random
from typing import Any

from dao_den_long.core.config import (
    DT,
    GRAVITY,
    ISLAND_RADIUS,
    JUMP_VELOCITY,
    TICK_RATE,
    TuningConfig,
    default_night1_lanterns,
    load_tuning,
)


def _r3(value: float) -> float:
    """Round float to 3 decimal places and normalize -0.0 to 0.0."""
    rounded = round(float(value), 3)
    return 0.0 if rounded == 0.0 else rounded


def _xz_dist(ax: float, az: float, bx: float, bz: float) -> float:
    """Horizontal XZ-plane Euclidean distance."""
    return math.hypot(ax - bx, az - bz)


@dataclass
class InputFrame:
    """Single-tick normalized player control state."""

    move: tuple[float, float] = (0.0, 0.0)
    cam_yaw_deg: float = 0.0
    jump: bool = False
    interact: bool = False
    pulse: bool = False
    dash: bool = False


@dataclass
class PlayerState:
    """State of May, the lantern keeper."""

    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    vy: float = 0.0
    carried: int = 0
    flames: int = 3
    invuln_ticks: int = 0
    pulse_cooldown_ticks: int = 0
    facing_yaw_deg: float = 0.0


@dataclass
class LanternState:
    """State of a Great Lantern (L1..L5)."""

    id: str
    x: float
    y: float
    z: float
    lit: bool = False
    deposited: int = 0


@dataclass
class ShadeState:
    """State of a Shadow Ink enemy (Bong Muc)."""

    id: str
    x: float
    y: float
    z: float
    state: str = "chase"
    stun_ticks: int = 0


@dataclass
class MoteState:
    """State of a collectible firefly mote."""

    id: str
    x: float
    y: float
    z: float


@dataclass
class _PrevButtons:
    jump: bool = False
    interact: bool = False
    pulse: bool = False


@dataclass
class Night1Simulation:
    """Deterministic Night 1 (Dao Ben) simulation complying with Test Contract v1.0."""

    seed: int = 42
    tuning: TuningConfig = field(default_factory=load_tuning)
    scenario: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        self._rng = random.Random(self.seed)
        self.tick = 0
        self.sim_tick = 0
        self.state = "playing"
        self.score = 0
        self._prev_buttons = _PrevButtons()
        self._mote_seq = 0
        self._shade_seq = 0

        sc = self.scenario or {}
        self.random_motes = bool(sc.get("random_motes", True))
        self.random_shades = bool(sc.get("random_shades", True))
        self.initial_time_left_s = float(sc.get("time_left_s", self.tuning.night1_duration_s))
        self.time_left_s = self.initial_time_left_s

        p_cfg = sc.get("player", {})
        p_pos = p_cfg.get("pos", [0.0, 0.0, 0.0])
        self.player = PlayerState(
            x=float(p_pos[0]),
            y=float(p_pos[1]),
            z=float(p_pos[2]),
            carried=int(p_cfg.get("carried", 0)),
            flames=int(p_cfg.get("flames", self.tuning.flames)),
        )

        # Lanterns L1..LN
        self.lanterns: list[LanternState] = [
            LanternState(id=lid, x=pos[0], y=pos[1], z=pos[2])
            for lid, pos in default_night1_lanterns(self.tuning.lantern_count_night1)
        ]
        lantern_by_id = {lantern.id: lantern for lantern in self.lanterns}
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

        # Motes
        self.motes: list[MoteState] = []
        if "motes" in sc:
            used_mote_ids = {
                str(item["id"])
                for item in sc["motes"]
                if isinstance(item, dict) and item.get("id") is not None
            }
            for item in sc["motes"]:
                if isinstance(item, dict):
                    pos = item["pos"]
                    if item.get("id") is not None:
                        mid = str(item["id"])
                    else:
                        mid = self._next_unique_id("M", used_mote_ids)
                        used_mote_ids.add(mid)
                else:
                    pos = item
                    mid = self._next_unique_id("M", used_mote_ids)
                    used_mote_ids.add(mid)
                self.motes.append(MoteState(id=mid, x=float(pos[0]), y=float(pos[1]), z=float(pos[2])))
        elif self.random_motes:
            for _ in range(15):
                self._spawn_random_mote()

        # Shades
        self.shades: list[ShadeState] = []
        if "shades" in sc:
            used_shade_ids = {
                str(item["id"])
                for item in sc["shades"]
                if isinstance(item, dict) and item.get("id") is not None
            }
            for item in sc["shades"]:
                if isinstance(item, dict):
                    pos = item["pos"]
                    if item.get("id") is not None:
                        sid = str(item["id"])
                    else:
                        sid = self._next_unique_id("S", used_shade_ids)
                        used_shade_ids.add(sid)
                    s_state = str(item.get("state", "chase"))
                else:
                    pos = item
                    sid = self._next_unique_id("S", used_shade_ids)
                    used_shade_ids.add(sid)
                    s_state = "chase"
                self.shades.append(
                    ShadeState(
                        id=sid,
                        x=float(pos[0]),
                        y=float(pos[1]),
                        z=float(pos[2]),
                        state=s_state,
                    )
                )
        elif self.random_shades:
            for _ in range(2):
                self._spawn_random_shade()

        max_dist = max(
            [ISLAND_RADIUS]
            + [math.hypot(self.player.x, self.player.z)]
            + [math.hypot(l.x, l.z) for l in self.lanterns]
            + [math.hypot(m.x, m.z) for m in self.motes]
            + [math.hypot(s.x, s.z) for s in self.shades]
        )
        self.arena_radius = max(ISLAND_RADIUS, max_dist + 20.0)

    def _next_unique_id(self, prefix: str, used_ids: set[str] | None = None) -> str:
        """Generate sequential unique ID (M1.., S1..) avoiding any existing IDs."""
        if used_ids is not None:
            existing = used_ids
        elif prefix == "M":
            existing = {m.id for m in self.motes}
        else:
            existing = {s.id for s in self.shades}

        while True:
            if prefix == "M":
                self._mote_seq += 1
                candidate = f"M{self._mote_seq}"
            else:
                self._shade_seq += 1
                candidate = f"S{self._shade_seq}"
            if candidate not in existing:
                return candidate

    def _spawn_random_mote(self) -> MoteState:
        angle = self._rng.uniform(0.0, 2.0 * math.pi)
        radius = math.sqrt(self._rng.uniform(5.0 ** 2, 38.0 ** 2))
        mote = MoteState(
            id=self._next_unique_id("M"),
            x=radius * math.cos(angle),
            y=0.0,
            z=radius * math.sin(angle),
        )
        self.motes.append(mote)
        return mote

    def _spawn_random_shade(self) -> ShadeState:
        for _ in range(20):
            angle = self._rng.uniform(0.0, 2.0 * math.pi)
            radius = self._rng.uniform(28.0, 42.0)
            sx = radius * math.cos(angle)
            sz = radius * math.sin(angle)
            if all(
                _xz_dist(sx, sz, l.x, l.z) >= self.tuning.safe_radius + 1.0
                for l in self.lanterns
                if l.lit
            ) and _xz_dist(sx, sz, self.player.x, self.player.z) >= 12.0:
                break
        shade = ShadeState(
            id=self._next_unique_id("S"),
            x=sx,
            y=1.0,
            z=sz,
            state="chase",
        )
        self.shades.append(shade)
        return shade

    def _enforce_safe_radius(self, shade: ShadeState) -> None:
        min_r = self.tuning.safe_radius + 0.002
        for lantern in self.lanterns:
            if not lantern.lit:
                continue
            dx = shade.x - lantern.x
            dz = shade.z - lantern.z
            dist = math.hypot(dx, dz)
            if dist <= self.tuning.safe_radius + 1e-6:
                if dist > 1e-9:
                    ux, uz = dx / dist, dz / dist
                else:
                    ux, uz = 1.0, 0.0
                shade.x = lantern.x + ux * min_r
                shade.z = lantern.z + uz * min_r

    def _finish_win_bonus(self) -> None:
        self.time_left_s = max(0.0, self.initial_time_left_s - (self.sim_tick / TICK_RATE))
        secs_left = int(math.floor(round(self.time_left_s, 6)))
        self.score += (
            secs_left * self.tuning.score.per_second_left
            + self.player.flames * self.tuning.score.per_flame_left
        )
        self.state = "won"

    def step(self, inputs: InputFrame | None = None) -> list[dict[str, Any]]:
        """Execute one 1/60s simulation tick and return emitted events."""
        if self.state != "playing":
            return []

        inp = inputs or InputFrame()
        self.tick += 1
        self.sim_tick += 1
        events: list[dict[str, Any]] = []

        jump_edge = inp.jump and not self._prev_buttons.jump
        interact_edge = inp.interact and not self._prev_buttons.interact
        pulse_edge = inp.pulse and not self._prev_buttons.pulse
        self._prev_buttons = _PrevButtons(
            jump=inp.jump,
            interact=inp.interact,
            pulse=inp.pulse,
        )

        # Decrement timers
        if self.player.invuln_ticks > 0:
            self.player.invuln_ticks -= 1
        if self.player.pulse_cooldown_ticks > 0:
            self.player.pulse_cooldown_ticks -= 1
        for shade in self.shades:
            if shade.state == "stunned":
                shade.stun_ticks -= 1
                if shade.stun_ticks <= 0:
                    shade.stun_ticks = 0
                    shade.state = "chase"

        # 1. Player movement (Contract C)
        mx, mz = float(inp.move[0]), float(inp.move[1])
        mag = math.hypot(mx, mz)
        if mag > 1.0:
            mx /= mag
            mz /= mag
        theta = math.radians(float(inp.cam_yaw_deg))
        cos_t = math.cos(theta)
        sin_t = math.sin(theta)
        wx = mx * cos_t + mz * sin_t
        wz = -mx * sin_t + mz * cos_t

        if mag > 1e-6:
            self.player.facing_yaw_deg = math.degrees(math.atan2(wx, wz))
        self.player.x += wx * self.tuning.player_speed * DT
        self.player.z += wz * self.tuning.player_speed * DT

        radial = math.hypot(self.player.x, self.player.z)
        if radial > self.arena_radius:
            scale = self.arena_radius / radial
            self.player.x *= scale
            self.player.z *= scale

        # Vertical jump & gravity (ground at y = 0)
        if jump_edge and self.player.y <= 1e-6:
            self.player.vy = JUMP_VELOCITY
        if self.player.y > 0.0 or self.player.vy != 0.0:
            self.player.y += self.player.vy * DT
            self.player.vy -= GRAVITY * DT
            if self.player.y <= 0.0:
                self.player.y = 0.0
                self.player.vy = 0.0

        # 2. Pick up motes
        remaining_motes: list[MoteState] = []
        for mote in self.motes:
            if (
                self.player.carried < self.tuning.carry_capacity
                and _xz_dist(self.player.x, self.player.z, mote.x, mote.z)
                <= self.tuning.pickup_radius + 1e-9
            ):
                self.player.carried += 1
                self.score += self.tuning.score.per_mote
                events.append(
                    {
                        "type": "event",
                        "tick": self.tick,
                        "name": "mote_picked",
                        "data": {"carried": self.player.carried},
                    }
                )
            else:
                remaining_motes.append(mote)
        self.motes = remaining_motes

        # 3. Pulse (rising edge)
        if (
            pulse_edge
            and self.player.carried >= self.tuning.pulse_cost
            and self.player.pulse_cooldown_ticks <= 0
        ):
            self.player.carried -= self.tuning.pulse_cost
            self.player.pulse_cooldown_ticks = round(self.tuning.pulse_cooldown_s * TICK_RATE)
            stunned_ids: list[str] = []
            stun_ticks = round(self.tuning.pulse_stun_s * TICK_RATE)
            for shade in self.shades:
                dx = shade.x - self.player.x
                dz = shade.z - self.player.z
                dist = math.hypot(dx, dz)
                if dist <= self.tuning.pulse_radius + 1e-9:
                    shade.state = "stunned"
                    shade.stun_ticks = stun_ticks
                    if dist > 1e-9:
                        ux, uz = dx / dist, dz / dist
                    else:
                        ux, uz = 1.0, 0.0
                    shade.x += ux * self.tuning.pulse_push_m
                    shade.z += uz * self.tuning.pulse_push_m
                    self._enforce_safe_radius(shade)
                    self.score += self.tuning.score.per_stun
                    stunned_ids.append(shade.id)
            events.append(
                {
                    "type": "event",
                    "tick": self.tick,
                    "name": "pulse",
                    "data": {"stunned_ids": stunned_ids},
                }
            )

        # 4. Interact / Deposit into nearest unlit lantern (rising edge)
        if interact_edge and self.player.carried > 0:
            candidates = [
                (
                    _xz_dist(self.player.x, self.player.z, l.x, l.z),
                    l.id,
                    l,
                )
                for l in self.lanterns
                if not l.lit
                and _xz_dist(self.player.x, self.player.z, l.x, l.z)
                <= self.tuning.interact_radius + 1e-9
            ]
            if candidates:
                candidates.sort(key=lambda item: (item[0], item[1]))
                target_lantern = candidates[0][2]
                needed = max(0, self.tuning.lantern_cost - target_lantern.deposited)
                amount = min(self.player.carried, needed)
                if amount > 0:
                    self.player.carried -= amount
                    target_lantern.deposited += amount
                    events.append(
                        {
                            "type": "event",
                            "tick": self.tick,
                            "name": "deposit",
                            "data": {
                                "lantern_id": target_lantern.id,
                                "amount": amount,
                                "deposited": target_lantern.deposited,
                            },
                        }
                    )
                    if target_lantern.deposited >= self.tuning.lantern_cost:
                        target_lantern.lit = True
                        self.score += self.tuning.score.per_lantern
                        events.append(
                            {
                                "type": "event",
                                "tick": self.tick,
                                "name": "lantern_lit",
                                "data": {"lantern_id": target_lantern.id},
                            }
                        )
                        for shade in self.shades:
                            self._enforce_safe_radius(shade)

                        if all(l.lit for l in self.lanterns):
                            self._finish_win_bonus()
                            events.append(
                                {
                                    "type": "event",
                                    "tick": self.tick,
                                    "name": "game_over",
                                    "data": {"result": "won", "reason": "all_lit"},
                                }
                            )
                            return events

        # 5. Periodic deterministic spawning (when enabled)
        if self.random_motes and self.sim_tick % 240 == 0 and len(self.motes) < 18:
            self._spawn_random_mote()
        if self.random_shades and self.sim_tick % 2100 == 0 and len(self.shades) < 5:
            new_shade = self._spawn_random_shade()
            events.append(
                {
                    "type": "event",
                    "tick": self.tick,
                    "name": "shade_spawned",
                    "data": {"id": new_shade.id},
                }
            )

        # 6. Shade chase & lit lantern safe_radius enforcement
        for shade in self.shades:
            if shade.state != "stunned":
                dx = self.player.x - shade.x
                dz = self.player.z - shade.z
                dist = math.hypot(dx, dz)
                if dist > 1e-9:
                    step_m = min(dist, self.tuning.shade_speed * DT)
                    shade.x += (dx / dist) * step_m
                    shade.z += (dz / dist) * step_m
            self._enforce_safe_radius(shade)

        # 7. Shade collision check
        if self.player.invuln_ticks <= 0:
            for shade in self.shades:
                if shade.state == "stunned":
                    continue
                if (
                    _xz_dist(self.player.x, self.player.z, shade.x, shade.z)
                    <= self.tuning.shade_hit_radius + 1e-9
                ):
                    self.player.flames = max(0, self.player.flames - 1)
                    dropped = int(math.floor(self.player.carried * self.tuning.hit_drop_ratio + 1e-9))
                    self.player.carried -= dropped
                    self.player.invuln_ticks = round(self.tuning.invuln_s * TICK_RATE)
                    events.append(
                        {
                            "type": "event",
                            "tick": self.tick,
                            "name": "player_hit",
                            "data": {
                                "by": "shade",
                                "flames": self.player.flames,
                                "dropped": dropped,
                            },
                        }
                    )
                    if self.player.flames <= 0:
                        self.time_left_s = max(0.0, self.initial_time_left_s - (self.sim_tick / TICK_RATE))
                        self.state = "lost"
                        events.append(
                            {
                                "type": "event",
                                "tick": self.tick,
                                "name": "game_over",
                                "data": {"result": "lost", "reason": "no_flames"},
                            }
                        )
                        return events
                    break

        # 8. Night timer / dawn check
        self.time_left_s = max(0.0, self.initial_time_left_s - (self.sim_tick / TICK_RATE))
        if self.time_left_s <= 1e-9:
            self.time_left_s = 0.0
            self.state = "lost"
            events.append(
                {
                    "type": "event",
                    "tick": self.tick,
                    "name": "game_over",
                    "data": {"result": "lost", "reason": "dawn"},
                }
            )

        return events

    def snapshot(self) -> dict[str, Any]:
        """Return Test Contract v1.0 snapshot record."""
        return {
            "type": "snapshot",
            "tick": self.tick,
            "sim_tick": self.sim_tick,
            "state": self.state,
            "time_left_s": _r3(self.time_left_s),
            "score": self.score,
            "player": {
                "pos": [_r3(self.player.x), _r3(self.player.y), _r3(self.player.z)],
                "flames": self.player.flames,
                "carried": self.player.carried,
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
                }
                for m in self.motes
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
