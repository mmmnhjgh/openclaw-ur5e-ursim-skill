import pytest

from ur5e_bridge.config import RobotConfig
from ur5e_bridge.guards import GuardViolation, MotionGuards


@pytest.fixture()
def config() -> RobotConfig:
    return RobotConfig.model_validate(
        {
            "robot_ip": "127.0.0.1",
            "workspace_bounds": {"x": [-0.5, 0.5], "y": [-0.5, 0.5], "z": [0.1, 0.8]},
            "named_poses": {"home": [0, -1.57, 1.57, -1.57, -1.57, 0]},
        }
    )


def test_rejects_non_remote_control(config: RobotConfig) -> None:
    guards = MotionGuards(config)
    with pytest.raises(GuardViolation, match="Remote Control"):
        guards.ensure_remote_control({"remote_control": False})


def test_rejects_blocking_safety_state(config: RobotConfig) -> None:
    guards = MotionGuards(config)
    with pytest.raises(GuardViolation, match="PROTECTIVE_STOP"):
        guards.ensure_motion_safe({"safety_status": "PROTECTIVE_STOP"})


def test_rejects_velocity_above_limit(config: RobotConfig) -> None:
    guards = MotionGuards(config)
    with pytest.raises(GuardViolation, match="max_joint_velocity"):
        guards.validate_motion_request(
            [0, 0, 0, 0, 0, 0], velocity=5.0, acceleration=0.5
        )


def test_rejects_workspace_violation(config: RobotConfig) -> None:
    guards = MotionGuards(config)
    with pytest.raises(GuardViolation, match="outside configured workspace"):
        guards.validate_current_tcp_pose([1.0, 0.0, 0.3, 0.0, 0.0, 0.0])
