from ur5e_bridge.actions import UR5eActions
from ur5e_bridge.config import RobotConfig
from ur5e_bridge.guards import GuardViolation


class FakeDashboard:
    def __init__(self) -> None:
        self.commands: list[str] = []

    def robot_mode(self) -> str:
        return "RUNNING"

    def safety_status(self) -> str:
        return "NORMAL"

    def program_state(self) -> str:
        return "PLAYING"

    def is_remote_control(self) -> bool:
        return True

    def pause(self) -> str:
        self.commands.append("pause")
        return "Pausing program"

    def play(self) -> str:
        self.commands.append("play")
        return "Starting program"

    def close_safety_popup(self) -> str:
        self.commands.append("close safety popup")
        return "closing safety popup"

    def unlock_protective_stop(self) -> str:
        self.commands.append("unlock protective stop")
        return "Protective stop releasing"

    def power_on(self) -> str:
        self.commands.append("power on")
        return "Powering on"

    def brake_release(self) -> str:
        self.commands.append("brake release")
        return "Brake releasing"


class FakeRTDE:
    def read_state(self) -> dict:
        return {
            "robot_mode": 7,
            "safety_status": 0,
            "runtime_state": 2,
            "speed_scaling": 1.0,
            "target_speed_fraction": 1.0,
            "actual_q": [0, -1.57, 1.57, -1.57, -1.57, 0],
            "actual_qd": [0, 0, 0, 0, 0, 0],
            "actual_TCP_pose": [0.0, 0.0, 0.3, 0.0, 0.0, 0.0],
            "actual_TCP_speed": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            "actual_digital_input_bits": 3,
            "actual_digital_output_bits": 1,
        }


class FakeURScript:
    def __init__(self) -> None:
        self.sent: list[tuple] = []

    def movej(self, joints, acceleration: float, velocity: float) -> str:
        self.sent.append(("movej", list(joints), acceleration, velocity))
        return "sent"

    def stopj(self, acceleration: float) -> str:
        self.sent.append(("stopj", acceleration))
        return "sent"

    def set_digital_output(self, output_id: int, value: bool) -> str:
        self.sent.append(("set_digital_output", output_id, value))
        return "sent"


def build_actions() -> UR5eActions:
    config = RobotConfig.model_validate(
        {
            "robot_ip": "127.0.0.1",
            "require_confirm_for_first_motion": True,
            "workspace_bounds": {"x": [-0.5, 0.5], "y": [-0.5, 0.5], "z": [0.1, 0.8]},
            "named_poses": {"home": [0, -1.57, 1.57, -1.57, -1.57, 0]},
        }
    )
    return UR5eActions(config, FakeDashboard(), FakeRTDE(), FakeURScript())


def test_status_contains_rtde_and_dashboard_fields() -> None:
    actions = build_actions()
    status = actions.get_status()
    assert status["robot_mode"] == "RUNNING"
    assert status["actual_q"][1] == -1.57
    assert status["actual_digital_input_bits"] == 3


def test_first_motion_requires_confirmation() -> None:
    actions = build_actions()
    try:
        actions.goto_named_pose("home", confirm=False)
    except GuardViolation as exc:
        assert "first motion" in str(exc)
    else:
        raise AssertionError("Expected first motion to require confirmation")


def test_named_pose_move_sends_script() -> None:
    actions = build_actions()
    result = actions.goto_named_pose("home", confirm=True)
    assert result["result"] == "sent"
    assert result["pose_name"] == "home"


def test_digital_output_requires_confirmation() -> None:
    actions = build_actions()
    try:
        actions.write_digital_output(0, True, confirm=False)
    except GuardViolation as exc:
        assert "confirmation" in str(exc).lower()
    else:
        raise AssertionError("Expected digital output write to require confirmation")
