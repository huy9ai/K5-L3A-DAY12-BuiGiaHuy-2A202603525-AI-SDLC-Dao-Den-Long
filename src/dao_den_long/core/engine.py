"""Deterministic simulation core for CP0 Hello 3D."""

from __future__ import annotations

from dataclasses import dataclass
import math
import random
from typing import Any


def _round6(value: float) -> float:
    """Round floats to 6 decimal places and normalize -0.0 to 0.0."""
    rounded = round(value, 6)
    return 0.0 if rounded == 0.0 else rounded


@dataclass(frozen=True)
class SimConfig:
    """Configuration for the CP0 deterministic simulation."""

    seed: int = 42
    dt: float = 1.0 / 60.0
    firefly_count: int = 5


@dataclass
class FireflyState:
    """State of a single orbiting firefly."""

    id: int
    orbit_radius: float
    angle: float
    speed: float
    base_height: float


@dataclass
class WorldState:
    """Mutable deterministic world state."""

    tick: int
    elapsed: float
    lantern_yaw: float
    lantern_bob: float
    lantern_glow: float
    fireflies: list[FireflyState]


class HelloSimulation:
    """Pure, deterministic CP0 simulation ready to be extended in Phase 1."""

    def __init__(self, config: SimConfig | None = None) -> None:
        self.config = config or SimConfig()
        self._rng = random.Random(self.config.seed)
        self.state = self._create_initial_state()

    def _create_initial_state(self) -> WorldState:
        fireflies: list[FireflyState] = []
        for idx in range(self.config.firefly_count):
            orbit_radius = 1.6 + self._rng.uniform(0.2, 2.2)
            angle = self._rng.uniform(0.0, 2.0 * math.pi)
            speed = self._rng.uniform(0.6, 1.5) * (1.0 if idx % 2 == 0 else -1.0)
            base_height = self._rng.uniform(0.8, 2.1)
            fireflies.append(
                FireflyState(
                    id=idx + 1,
                    orbit_radius=orbit_radius,
                    angle=angle,
                    speed=speed,
                    base_height=base_height,
                )
            )
        return WorldState(
            tick=0,
            elapsed=0.0,
            lantern_yaw=0.0,
            lantern_bob=0.0,
            lantern_glow=1.0,
            fireflies=fireflies,
        )

    def reset(self) -> None:
        """Reset simulation to initial deterministic state."""
        self._rng = random.Random(self.config.seed)
        self.state = self._create_initial_state()

    def step(self, action: dict[str, Any] | None = None) -> WorldState:
        """Advance simulation by one fixed timestep."""
        dt = self.config.dt
        self.state.tick += 1
        self.state.elapsed = self.state.tick * dt

        if action:
            if action.get("pulse"):
                self.state.lantern_glow = min(2.4, self.state.lantern_glow + 0.85)
            yaw_delta = action.get("yaw_delta", 0.0)
            if isinstance(yaw_delta, (int, float)):
                self.state.lantern_yaw = (self.state.lantern_yaw + float(yaw_delta)) % (2.0 * math.pi)

        self.state.lantern_yaw = (self.state.lantern_yaw + 0.65 * dt) % (2.0 * math.pi)
        self.state.lantern_bob = 0.14 * math.sin(self.state.elapsed * 2.2)
        self.state.lantern_glow = max(1.0, self.state.lantern_glow - 1.4 * dt)

        for ff in self.state.fireflies:
            ff.angle = (ff.angle + ff.speed * dt) % (2.0 * math.pi)

        return self.state

    def snapshot(self) -> dict[str, Any]:
        """Return canonical JSON-serializable state snapshot."""
        firefly_views = []
        for ff in self.state.fireflies:
            x = ff.orbit_radius * math.cos(ff.angle)
            z = ff.orbit_radius * math.sin(ff.angle)
            y = ff.base_height + 0.18 * math.sin(self.state.elapsed * 3.0 + ff.id)
            firefly_views.append(
                {
                    "id": ff.id,
                    "x": _round6(x),
                    "y": _round6(y),
                    "z": _round6(z),
                }
            )

        return {
            "phase": "cp0",
            "seed": self.config.seed,
            "tick": self.state.tick,
            "elapsed": _round6(self.state.elapsed),
            "lantern": {
                "yaw": _round6(self.state.lantern_yaw),
                "bob": _round6(self.state.lantern_bob),
                "glow": _round6(self.state.lantern_glow),
            },
            "fireflies": firefly_views,
        }
