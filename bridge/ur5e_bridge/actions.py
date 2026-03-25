from __future__ import annotations

from typing import Any, Sequence

from .config import RobotConfig
from .dashboard import DashboardClient
from .guards import GuardViolation, MotionGuards
from .rtde_state import RTDEStateClient
from .urscript import URScriptClient


ROBOT_MODE_LABELS = {
    -1: "UNKNOWN",
    0: "DISCONNECTED",
    1: "CONFIRM_SAFETY",
    2: "BOOTING",
    3: "POWER_OFF",
    4: "POWER_ON",
    5: "IDLE",
    6: "BACKDRIVE",
    7: "RUNNING",
}

RUNTIME_STATE_LABELS = {
    0: "STOPPING",
    1: "STOPPED",
    2: "PLAYING",
    3: "PAUSING",
    4: "PAUSED",
    5: "RESUMING",
}

SAFETY_STATUS_LABELS = {
    0: "NORMAL",
    1: "REDUCED",
    2: "PROTECTIVE_STOP",
    3: "RECOVERY",
    4: "SAFEGUARD_STOP",
    5: "SYSTEM_EMERGENCY_STOP",
    6: "ROBOT_EMERGENCY_STOP",
    7: "VIOLATION",
    8: "FAULT",
    9: "AUTOMATIC_MODE_SAFEGUARD_STOP",
    10: "SYSTEM_THREE_POSITION_ENABLING_STOP",
}


class UR5eActions:
    def __init__(
        self,
        config: RobotConfig,
        dashboard: DashboardClient,
        rtde_state: RTDEStateClient,
        urscript: URScriptClient,
    ) -> None:
        self.config = config
        self.dashboard = dashboard
        self.rtde_state = rtde_state
        self.urscript = urscript
        self.guards = MotionGuards(config)
        self._first_motion_sent = False

    def get_status(self) -> dict[str, Any]:
        dashboard_robot_mode = self.dashboard.robot_mode()
        dashboard_safety_status = self.dashboard.safety_status()
        program_state = self.dashboard.program_state()
        remote_control = self.dashboard.is_remote_control()
        rtde_state = self.rtde_state.read_state()

        return {
            "robot_ip": self.config.robot_ip,
            "simulation": self.config.simulation,
            "remote_control": remote_control,
            "robot_mode": dashboard_robot_mode,
            "robot_mode_rtde": ROBOT_MODE_LABELS.get(
                int(rtde_state.get("robot_mode", -1)), "UNKNOWN"
            ),
            "safety_status": dashboard_safety_status,
            "safety_status_rtde": SAFETY_STATUS_LABELS.get(
                int(rtde_state.get("safety_status", -1)), "UNKNOWN"
            ),
            "program_state": program_state,
            "runtime_state": RUNTIME_STATE_LABELS.get(
                int(rtde_state.get("runtime_state", -1)), "UNKNOWN"
            ),
            "speed_scaling": float(rtde_state.get("speed_scaling", 0.0)),
            "target_speed_fraction": float(
                rtde_state.get("target_speed_fraction", 0.0)
            ),
            "actual_q": list(rtde_state.get("actual_q", [])),
            "actual_qd": list(rtde_state.get("actual_qd", [])),
            "actual_tcp_pose": list(rtde_state.get("actual_TCP_pose", [])),
            "actual_tcp_speed": list(rtde_state.get("actual_TCP_speed", [])),
            "actual_digital_input_bits": int(
                rtde_state.get("actual_digital_input_bits", 0)
            ),
            "actual_digital_output_bits": int(
                rtde_state.get("actual_digital_output_bits", 0)
            ),
        }

    def goto_named_pose(self, name: str, confirm: bool = False) -> dict[str, Any]:
        if name not in self.config.named_poses:
            raise GuardViolation(
                f"Unknown named pose '{name}'. Available poses: {sorted(self.config.named_poses)}"
            )
        return self.move_joints(
            self.config.named_poses[name], confirm=confirm, pose_name=name
        )

    def move_joints(
        self,
        joints: Sequence[float],
        velocity: float | None = None,
        acceleration: float | None = None,
        confirm: bool = False,
        pose_name: str | None = None,
    ) -> dict[str, Any]:
        status = self.get_status()
        self.guards.ensure_remote_control(status)
        self.guards.ensure_motion_safe(status)
        self.guards.validate_current_tcp_pose(status.get("actual_tcp_pose"))

        velocity = velocity or self.config.default_joint_velocity
        acceleration = acceleration or self.config.default_joint_acceleration
        validated_joints = self.guards.validate_motion_request(
            joints, velocity, acceleration
        )

        if self.config.require_confirm_for_first_motion and not self._first_motion_sent:
            self.guards.ensure_confirmation(
                confirm, "first motion in this bridge session"
            )

        result = self.urscript.movej(
            validated_joints, acceleration=acceleration, velocity=velocity
        )
        self._first_motion_sent = True
        return {
            "command": "move_joints",
            "pose_name": pose_name,
            "result": result,
            "target_joints": validated_joints,
            "velocity": velocity,
            "acceleration": acceleration,
        }

    def stop_motion(self, acceleration: float | None = None) -> dict[str, Any]:
        stop_acceleration = acceleration or self.config.default_joint_acceleration
        if (
            stop_acceleration <= 0
            or stop_acceleration > self.config.max_joint_acceleration
        ):
            raise GuardViolation(
                f"Stop acceleration {stop_acceleration} exceeds configured max_joint_acceleration={self.config.max_joint_acceleration}."
            )
        return {
            "command": "stop_motion",
            "result": self.urscript.stopj(stop_acceleration),
            "acceleration": stop_acceleration,
        }

    def pause_program(self) -> dict[str, Any]:
        return {"command": "pause_program", "result": self.dashboard.pause()}

    def resume_program(self) -> dict[str, Any]:
        return {"command": "resume_program", "result": self.dashboard.play()}

    def read_digital_io(self) -> dict[str, Any]:
        status = self.get_status()
        inputs = self._bitfield_to_map(status["actual_digital_input_bits"])
        outputs = self._bitfield_to_map(status["actual_digital_output_bits"])
        return {
            "command": "read_digital_io",
            "inputs": inputs,
            "outputs": outputs,
        }

    def write_digital_output(
        self, output_id: int, value: bool, confirm: bool = False
    ) -> dict[str, Any]:
        if output_id < 0 or output_id > 7:
            raise GuardViolation(
                "Only standard digital outputs 0-7 are supported in this scaffold."
            )
        self.guards.ensure_confirmation(confirm, f"write digital output {output_id}")
        result = self.urscript.set_digital_output(output_id=output_id, value=value)
        return {
            "command": "write_digital_output",
            "output_id": output_id,
            "value": value,
            "result": result,
        }

    def recover_robot(self, confirm: bool = False) -> dict[str, Any]:
        self.guards.ensure_confirmation(
            confirm, "recovery actions can change robot safety state"
        )
        status = self.get_status()
        steps: list[str] = []

        if "PROTECTIVE_STOP" in status["safety_status"].upper():
            steps.append(self.dashboard.close_safety_popup())
            steps.append(self.dashboard.unlock_protective_stop())

        if status["robot_mode"].upper() == "POWER_OFF":
            steps.append(self.dashboard.power_on())
            steps.append(self.dashboard.brake_release())

        if not steps:
            steps.append("No recovery action required.")

        return {"command": "recover_robot", "result": steps}

    @staticmethod
    def _bitfield_to_map(bitfield: int, width: int = 8) -> dict[str, bool]:
        return {str(index): bool(bitfield & (1 << index)) for index in range(width)}
