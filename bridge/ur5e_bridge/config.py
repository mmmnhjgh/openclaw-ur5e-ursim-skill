from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class PayloadConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mass_kg: float = Field(default=0.0, ge=0.0, le=20.0)
    center_of_gravity_m: List[float] = Field(
        default_factory=lambda: [0.0, 0.0, 0.0], min_length=3, max_length=3
    )


class WorkspaceBounds(BaseModel):
    model_config = ConfigDict(extra="forbid")

    x: Tuple[float, float]
    y: Tuple[float, float]
    z: Tuple[float, float]

    @model_validator(mode="after")
    def validate_ranges(self) -> "WorkspaceBounds":
        for axis in ("x", "y", "z"):
            low, high = getattr(self, axis)
            if low >= high:
                raise ValueError(
                    f"workspace axis {axis} must be [min, max] with min < max"
                )
        return self


class RobotConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    robot_ip: str = Field(min_length=1)
    dashboard_port: int = Field(default=29999, ge=1, le=65535)
    rtde_port: int = Field(default=30004, ge=1, le=65535)
    urscript_port: int = Field(default=30002, ge=1, le=65535)
    connect_timeout_s: float = Field(default=2.0, gt=0.0, le=30.0)
    simulation: bool = Field(default=True)
    require_confirm_for_first_motion: bool = Field(default=True)
    default_joint_velocity: float = Field(default=0.2, gt=0.0, le=2.0)
    default_joint_acceleration: float = Field(default=0.4, gt=0.0, le=5.0)
    max_joint_velocity: float = Field(default=0.5, gt=0.0, le=3.0)
    max_joint_acceleration: float = Field(default=0.8, gt=0.0, le=10.0)
    max_tcp_speed: float = Field(default=0.25, gt=0.0, le=3.0)
    tcp_offset: List[float] = Field(
        default_factory=lambda: [0.0] * 6, min_length=6, max_length=6
    )
    payload: PayloadConfig = Field(default_factory=PayloadConfig)
    workspace_bounds: WorkspaceBounds
    named_poses: Dict[str, List[float]] = Field(default_factory=dict)

    @field_validator("named_poses")
    @classmethod
    def validate_named_poses(
        cls, value: Dict[str, List[float]]
    ) -> Dict[str, List[float]]:
        for name, joints in value.items():
            if len(joints) != 6:
                raise ValueError(
                    f"named pose '{name}' must contain exactly 6 joint values"
                )
        return value

    @model_validator(mode="after")
    def validate_joint_limits(self) -> "RobotConfig":
        if self.default_joint_velocity > self.max_joint_velocity:
            raise ValueError("default_joint_velocity cannot exceed max_joint_velocity")
        if self.default_joint_acceleration > self.max_joint_acceleration:
            raise ValueError(
                "default_joint_acceleration cannot exceed max_joint_acceleration"
            )
        return self


def load_config(path: str | Path) -> RobotConfig:
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"UR5e config file not found: {config_path}")

    with config_path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}

    return RobotConfig.model_validate(data)
