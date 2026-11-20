"""Standardized map geometry, spawn grids, ramps, launch pads, and obstacles for Nights 1-3."""

from __future__ import annotations

from dataclasses import dataclass
import math


def _polar(cx: float, cz: float, radius: float, angle_deg: float, y: float = 0.0) -> tuple[float, float, float]:
    """Convert polar coords (angle CCW from +X looking down +Y) to (x, y, z)."""
    rad = math.radians(angle_deg)
    return (
        round(cx + radius * math.cos(rad), 3),
        round(y, 3),
        round(cz + radius * math.sin(rad), 3),
    )


@dataclass(frozen=True)
class LaunchPad:
    """Jump/launch pad propelling May along a fixed ballistic arc."""

    x: float
    y: float
    z: float
    radius: float
    vy: float
    vx: float
    vz: float


@dataclass(frozen=True)
class RampDef:
    """Straight radial ramp connecting Tier 0 (Y=0) to Tier 1 (Y=3)."""

    angle_deg: float
    ux: float
    uz: float
    tx: float
    tz: float
    inner_r: float = 24.0
    outer_r: float = 30.0
    half_width: float = 1.5
    top_y: float = 3.0


@dataclass(frozen=True)
class MapDefinition:
    """Complete map geometry and spawn tables for one Night."""

    night: int
    name: str
    intro_quote: str
    duration_s: float
    player_spawn: tuple[float, float, float]
    lantern_spawns: tuple[tuple[str, tuple[float, float, float]], ...]
    mote_spawns: tuple[tuple[float, float, float], ...]
    shade_spawns: tuple[tuple[float, float, float], ...]
    charm_spawns: tuple[tuple[str, tuple[float, float, float]], ...]
    launch_pads: tuple[LaunchPad, ...]
    ramps: tuple[RampDef, ...]
    shade_speed: float
    shade_spawn_interval: int
    max_shades: int
    has_drifters: bool
    has_wind: bool
    bell_tower_radius: float = 0.0
    bell_tower_top_y: float = 0.0

    def ground_height(self, x: float, z: float) -> float | None:
        """Return terrain height Y at (x, z), or None when over the cloud sea."""
        if self.night == 1:
            return 0.0 if math.hypot(x, z) <= 40.0 else None

        if self.night == 2:
            if math.hypot(x, z) <= 28.0 or math.hypot(x - 70.0, z) <= 28.0:
                return 0.0
            if 26.0 <= x <= 44.0 and -2.0 <= z <= 2.0:
                return 0.0
            return None

        # Night 3: Đảo Chuông
        r = math.hypot(x, z)
        if r > 45.0:
            return None
        if r <= 8.0:
            return 6.0
        if 12.0 <= r <= 24.0 and z > 0.0:
            return 3.0
        for ramp in self.ramps:
            s = x * ramp.ux + z * ramp.uz
            perp = abs(x * ramp.tx + z * ramp.tz)
            # Extend inner check by 0.1m so outer corners at r=24 join Tier 1 seamlessly
            if (ramp.inner_r - 0.1) <= s <= ramp.outer_r and perp <= ramp.half_width:
                t = (ramp.outer_r - s) / (ramp.outer_r - ramp.inner_r)
                return max(0.0, min(ramp.top_y, ramp.top_y * t))
        return 0.0

    def is_blocked_obstacle(self, x: float, y: float, z: float) -> bool:
        """Check solid cylindrical obstacle (Night 3 bell tower)."""
        if self.bell_tower_radius > 0.0 and y < self.bell_tower_top_y:
            return math.hypot(x, z) < self.bell_tower_radius
        return False

    def _can_step(self, old_y: float, x: float, z: float, *, allow_void: bool) -> bool:
        if self.is_blocked_obstacle(x, old_y, z):
            return False
        target_y = self.ground_height(x, z)
        if target_y is None:
            return allow_void
        return target_y <= old_y + 0.55

    def resolve_horizontal_move(
        self,
        old_x: float,
        old_y: float,
        old_z: float,
        new_x: float,
        new_z: float,
        *,
        allow_void: bool,
    ) -> tuple[float, float, bool]:
        """Resolve horizontal movement against cliffs, bell tower, and optional void boundary."""
        if self._can_step(old_y, new_x, new_z, allow_void=allow_void):
            return new_x, new_z, False
        if self._can_step(old_y, new_x, old_z, allow_void=allow_void):
            return new_x, old_z, True
        if self._can_step(old_y, old_x, new_z, allow_void=allow_void):
            return old_x, new_z, True
        return old_x, old_z, True


def _make_launch_pad_to(
    x: float, y: float, z: float, target_x: float, target_z: float, vy: float, h_speed: float
) -> LaunchPad:
    dx = target_x - x
    dz = target_z - z
    dist = math.hypot(dx, dz) or 1.0
    return LaunchPad(
        x=x, y=y, z=z, radius=1.0, vy=vy, vx=(dx / dist) * h_speed, vz=(dz / dist) * h_speed
    )


def build_night_map(night: int) -> MapDefinition:
    """Build standardized map definition for Night 1, 2, or 3 (Contract v1.2 durations)."""
    if night == 1:
        mote_spawns = (
            tuple(_polar(0.0, 0.0, 12.0, i * 45.0) for i in range(8))
            + tuple(_polar(0.0, 0.0, 33.0, i * 22.5) for i in range(16))
        )
        shade_spawns = tuple(_polar(0.0, 0.0, 37.0, 15.0 + i * 30.0) for i in range(12))
        return MapDefinition(
            night=1,
            name="Đêm 1 — Đảo Bến",
            intro_quote="Ông Đăng: \"Đèn thắp rồi vẫn cạn dầu! Hãy giữ ít nhất 3/5 Đèn Lồng sáng tới bình minh.\"",
            duration_s=240.0,
            player_spawn=(0.0, 0.0, 0.0),
            lantern_spawns=(
                ("L1", (0.0, 0.0, 25.0)),
                ("L2", (23.8, 0.0, 7.7)),
                ("L3", (14.7, 0.0, -20.2)),
                ("L4", (-14.7, 0.0, -20.2)),
                ("L5", (-23.8, 0.0, 7.7)),
            ),
            mote_spawns=mote_spawns,
            shade_spawns=shade_spawns,
            charm_spawns=(),
            launch_pads=(),
            ramps=(),
            shade_speed=4.0,
            shade_spawn_interval=480,
            max_shades=6,
            has_drifters=False,
            has_wind=False,
        )

    if night == 2:
        mote_spawns = (
            tuple(_polar(0.0, 0.0, 10.0, i * 90.0) for i in range(4))
            + tuple(_polar(0.0, 0.0, 22.0, i * 45.0) for i in range(8))
            + tuple(_polar(70.0, 0.0, 10.0, i * 90.0) for i in range(4))
            + tuple(_polar(70.0, 0.0, 22.0, i * 45.0) for i in range(8))
        )
        shade_spawns = (
            tuple(_polar(0.0, 0.0, 26.0, 22.5 + i * 45.0) for i in range(8))
            + tuple(_polar(70.0, 0.0, 26.0, 22.5 + i * 45.0) for i in range(8))
        )
        return MapDefinition(
            night=2,
            name="Đêm 2 — Đảo Cau",
            intro_quote="Ông Đăng: \"Giữ sáng ít nhất 4/6 đèn trên hai bờ Đảo Cau tới bình minh — coi chừng Bóng Mực hút dầu và Gió Lạc!\"",
            duration_s=270.0,
            player_spawn=(0.0, 0.0, 0.0),
            lantern_spawns=(
                ("L1", (0.0, 0.0, 20.0)),
                ("L2", (17.0, 0.0, -10.0)),
                ("L3", (-17.0, 0.0, -10.0)),
                ("L4", (70.0, 0.0, 20.0)),
                ("L5", (87.0, 0.0, -10.0)),
                ("L6", (53.0, 0.0, -10.0)),
            ),
            mote_spawns=mote_spawns,
            shade_spawns=shade_spawns,
            charm_spawns=(("C1", (35.0, 0.0, 0.0)),),
            launch_pads=(
                _make_launch_pad_to(20.0, 0.0, 18.0, 70.0, 0.0, vy=14.0, h_speed=24.0),
                _make_launch_pad_to(50.0, 0.0, -18.0, 0.0, 0.0, vy=14.0, h_speed=24.0),
            ),
            ramps=(),
            shade_speed=4.0,
            shade_spawn_interval=420,
            max_shades=8,
            has_drifters=True,
            has_wind=False,
        )

    if night == 3:
        mote_spawns = (
            tuple(_polar(0.0, 0.0, 34.0, i * 20.0, y=0.0) for i in range(18))
            + tuple(_polar(0.0, 0.0, 18.0, (i + 1) * 20.0, y=3.0) for i in range(8))
            + tuple(_polar(0.0, 0.0, 5.0, 45.0 + i * 90.0, y=6.0) for i in range(4))
        )
        shade_spawns = tuple(_polar(0.0, 0.0, 43.0, i * 22.5, y=0.0) for i in range(16))
        ramps = tuple(
            RampDef(
                angle_deg=deg,
                ux=math.cos(math.radians(deg)),
                uz=math.sin(math.radians(deg)),
                tx=-math.sin(math.radians(deg)),
                tz=math.cos(math.radians(deg)),
            )
            for deg in (30.0, 150.0)
        )
        return MapDefinition(
            night=3,
            name="Đêm 3 — Đảo Chuông",
            intro_quote="Ông Đăng: \"Đêm cuối 5 phút trên Đảo Chuông! Hãy châm dầu và giữ sáng tối thiểu 5/7 đèn tới lúc bình minh ló dạng.\"",
            duration_s=300.0,
            player_spawn=(0.0, 0.0, -15.0),
            lantern_spawns=(
                ("L1", (0.0, 6.0, 6.0)),
                ("L2", (18.0, 3.0, 10.0)),
                ("L3", (-18.0, 3.0, 10.0)),
                ("L4", (35.0, 0.0, -10.0)),
                ("L5", (-35.0, 0.0, -10.0)),
                ("L6", (20.0, 0.0, -35.0)),
                ("L7", (-20.0, 0.0, -35.0)),
            ),
            mote_spawns=mote_spawns,
            shade_spawns=shade_spawns,
            charm_spawns=(("C1", (30.0, 0.0, 25.0)), ("C2", (-30.0, 0.0, 25.0))),
            launch_pads=(LaunchPad(x=0.0, y=3.0, z=13.0, radius=1.0, vy=12.0, vx=0.0, vz=-8.0),),
            ramps=ramps,
            shade_speed=4.5,
            shade_spawn_interval=360,
            max_shades=10,
            has_drifters=True,
            has_wind=True,
            bell_tower_radius=2.0,
            bell_tower_top_y=14.0,
        )

    raise ValueError(f"Unsupported night {night}; expected 1, 2, or 3")
