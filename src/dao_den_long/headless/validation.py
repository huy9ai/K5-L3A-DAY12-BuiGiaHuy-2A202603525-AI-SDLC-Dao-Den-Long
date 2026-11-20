"""Strict JSON schema validation for Test Contract v1.0 inputs and scenarios."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any


class ContractInputError(ValueError):
    """Raised when --inputs or --scenario fails Test Contract v1.0 validation (exit code 2)."""


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _is_num(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def _validate_pos3(value: Any, label: str) -> list[float]:
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        raise ContractInputError(f"{label} must be a 3-element array [x, y, z]")
    out: list[float] = []
    for idx, coord in enumerate(value):
        if not _is_num(coord):
            raise ContractInputError(f"{label}[{idx}] must be a finite number")
        out.append(float(coord))
    return out


def _read_json_dict(path: Path, kind: str) -> dict[str, Any]:
    if not path.is_file():
        raise ContractInputError(f"{kind} file not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ContractInputError(f"Invalid JSON in {kind} file '{path}': {exc}") from exc
    if not isinstance(data, dict):
        raise ContractInputError(f"{kind} root must be a JSON object")
    return data


def load_and_validate_inputs(path: Path) -> dict[int, dict[str, Any]]:
    """Load and validate Test Contract v1.0 inputs JSON, keyed by tick."""
    data = _read_json_dict(path, "inputs")
    frames = data.get("frames")
    if not isinstance(frames, list):
        raise ContractInputError("inputs must contain a 'frames' array")

    frames_by_tick: dict[int, dict[str, Any]] = {}
    last_tick = -1
    for idx, frame in enumerate(frames):
        if not isinstance(frame, dict):
            raise ContractInputError(f"frames[{idx}] must be an object")
        tick = frame.get("tick")
        if not _is_int(tick) or tick < 0:
            raise ContractInputError(f"frames[{idx}].tick must be a non-negative integer")
        if tick <= last_tick:
            raise ContractInputError(
                f"frames[{idx}].tick ({tick}) must strictly increase (previous {last_tick})"
            )
        last_tick = tick

        if "move" in frame:
            move = frame["move"]
            if not isinstance(move, (list, tuple)) or len(move) != 2:
                raise ContractInputError(f"frames[{idx}].move must be [x, z]")
            for c_idx, comp in enumerate(move):
                if not _is_num(comp) or not (-1.0 <= float(comp) <= 1.0):
                    raise ContractInputError(
                        f"frames[{idx}].move[{c_idx}] must be a number in [-1, 1]"
                    )

        if "cam_yaw_deg" in frame and not _is_num(frame["cam_yaw_deg"]):
            raise ContractInputError(f"frames[{idx}].cam_yaw_deg must be a finite number")

        for btn in ("jump", "interact", "pulse", "dash"):
            if btn in frame and not isinstance(frame[btn], bool):
                raise ContractInputError(f"frames[{idx}].{btn} must be a boolean")

        frames_by_tick[tick] = frame

    return frames_by_tick


def load_and_validate_scenario(path: Path, lantern_count: int = 5) -> dict[str, Any]:
    """Load and validate Test Contract v1.0 scenario JSON."""
    data = _read_json_dict(path, "scenario")
    valid_lantern_ids = {f"L{i + 1}" for i in range(lantern_count)}

    if "player" in data:
        player = data["player"]
        if not isinstance(player, dict):
            raise ContractInputError("scenario.player must be an object")
        if "pos" in player:
            _validate_pos3(player["pos"], "scenario.player.pos")
        if "carried" in player and (not _is_int(player["carried"]) or player["carried"] < 0):
            raise ContractInputError("scenario.player.carried must be a non-negative integer")
        if "flames" in player and (not _is_int(player["flames"]) or player["flames"] < 0):
            raise ContractInputError("scenario.player.flames must be a non-negative integer")

    for flag in ("random_motes", "random_shades"):
        if flag in data and not isinstance(data[flag], bool):
            raise ContractInputError(f"scenario.{flag} must be a boolean")

    if "time_left_s" in data and (not _is_num(data["time_left_s"]) or float(data["time_left_s"]) < 0.0):
        raise ContractInputError("scenario.time_left_s must be >= 0")

    if "motes" in data:
        if not isinstance(data["motes"], list):
            raise ContractInputError("scenario.motes must be an array")
        for idx, item in enumerate(data["motes"]):
            if isinstance(item, dict):
                _validate_pos3(item.get("pos"), f"scenario.motes[{idx}].pos")
            else:
                _validate_pos3(item, f"scenario.motes[{idx}]")

    if "shades" in data:
        if not isinstance(data["shades"], list):
            raise ContractInputError("scenario.shades must be an array")
        for idx, item in enumerate(data["shades"]):
            if isinstance(item, dict):
                _validate_pos3(item.get("pos"), f"scenario.shades[{idx}].pos")
            else:
                _validate_pos3(item, f"scenario.shades[{idx}]")

    if "lanterns" in data:
        if not isinstance(data["lanterns"], list):
            raise ContractInputError("scenario.lanterns must be an array")
        for idx, item in enumerate(data["lanterns"]):
            if not isinstance(item, dict):
                raise ContractInputError(f"scenario.lanterns[{idx}] must be an object")
            lid = item.get("id")
            if lid not in valid_lantern_ids:
                raise ContractInputError(
                    f"scenario.lanterns[{idx}].id must be one of {sorted(valid_lantern_ids)}"
                )
            if "pos" in item:
                _validate_pos3(item["pos"], f"scenario.lanterns[{idx}].pos")
            if "deposited" in item and (not _is_int(item["deposited"]) or item["deposited"] < 0):
                raise ContractInputError(f"scenario.lanterns[{idx}].deposited must be >= 0")
            if "lit" in item and not isinstance(item["lit"], bool):
                raise ContractInputError(f"scenario.lanterns[{idx}].lit must be a boolean")

    return data
