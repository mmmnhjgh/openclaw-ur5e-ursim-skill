from __future__ import annotations

from typing import Any, Iterable, Sequence

from .config import RobotConfig


MOTION_BLOCKING_SAFETY_STATES = {
    "PROTECTIVE_STOP",
    "RECOVERY",
    "SAFEGUARD_STOP",
    "SYSTEM_EMERGENCY_STOP",
    "ROBOT_EMERGENCY_STOP",
    "VIOLATION",
    "FAULT",
    "AUTOMATIC_MODE_SAFEGUARD_STOP",
    "SYSTEM_THREE_POSITION_ENABLING_STOP",
}


class GuardViolation(RuntimeError):
    """Raised when a requested robot action violates policy."""


class MotionGuards:
    def __init__(self, config: RobotConfig) -> None:
        self.config = config

    def ensure_remote_control(self, status: dict[str, Any]) -> None:
        if not status.get("remote_control", False):
            raise GuardViolation("Robot is not in Remote Control mode.")

    def ensure_motion_safe(self, status: dict[str, Any]) -> None:
        safety_status = str(status.get("safety_status", "UNKNOWN")).upper()
        if safety_status in MOTION_BLOCKING_SAFETY_STATES:
            raise GuardViolation(
                f"Motion blocked because safety_status={safety_status}."
            )

    def ensure_confirmation(self, confirm: bool, reason: str) -> None:
        if not confirm:
            raise GuardViolation(f"Operator confirmation required: {reason}")

    def validate_joint_target(self, joints: Sequence[float]) -> list[float]:
        if len(joints) != 6:
            raise GuardViolation("Joint target must contain exactly 6 values.")

        validated = [float(value) for value in joints]
        for index, value in enumerate(validated):
            if not -6.28319 <= value <= 6.28319:
                raise GuardViolation(
                    f"Joint {index} target {value} rad is outside the allowed range [-2pi, 2pi]."
                )
        return validated

    def validate_motion_request(
        self, joints: Sequence[float], velocity: float, acceleration: float
    ) -> list[float]:
        validated = self.validate_joint_target(joints)
        if velocity <= 0 or velocity > self.config.max_joint_velocity:
            raise GuardViolation(
                f"Requested joint velocity {velocity} exceeds configured max_joint_velocity={self.config.max_joint_velocity}."
            )
        if acceleration <= 0 or acceleration > self.config.max_joint_acceleration:
            raise GuardViolation(
                f"Requested joint acceleration {acceleration} exceeds configured max_joint_acceleration={self.config.max_joint_acceleration}."
            )
        return validated

    def validate_current_tcp_pose(self, tcp_pose: Iterable[float] | None) -> None:
        if tcp_pose is None:
            return
        pose = list(tcp_pose)
        if len(pose) < 3:
            return

        bounds = self.config.workspace_bounds
        x, y, z = pose[:3]
        if not bounds.x[0] <= x <= bounds.x[1]:
            raise GuardViolation(
                f"Current TCP x={x} is outside configured workspace bounds {bounds.x}."
            )
        if not bounds.y[0] <= y <= bounds.y[1]:
            raise GuardViolation(
                f"Current TCP y={y} is outside configured workspace bounds {bounds.y}."
            )
        if not bounds.z[0] <= z <= bounds.z[1]:
            raise GuardViolation(
                f"Current TCP z={z} is outside configured workspace bounds {bounds.z}."
            )
