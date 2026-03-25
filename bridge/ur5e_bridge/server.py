from __future__ import annotations

import os
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, AsyncIterator

from mcp.server.fastmcp import Context, FastMCP
from mcp.server.session import ServerSession
from pydantic import BaseModel, ConfigDict, Field

from .actions import UR5eActions
from .config import RobotConfig, load_config
from .dashboard import DashboardClient
from .guards import GuardViolation
from .rtde_state import RTDEStateClient
from .urscript import URScriptClient


DEFAULT_CONFIG_PATH = (
    Path(__file__).resolve().parents[2]
    / "skills"
    / "ur5e-control"
    / "config.example.yaml"
)


class NamedPoseInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(
        description="Configured named pose such as home, approach, or park.",
        min_length=1,
    )
    confirm: bool = Field(
        default=False, description="Set true to confirm the motion should execute."
    )


class MoveJointsInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    joints: list[float] = Field(
        description="Exactly 6 joint values in radians.", min_length=6, max_length=6
    )
    velocity: float | None = Field(
        default=None, description="Optional joint velocity in rad/s.", gt=0.0
    )
    acceleration: float | None = Field(
        default=None, description="Optional joint acceleration in rad/s^2.", gt=0.0
    )
    confirm: bool = Field(
        default=False, description="Set true to confirm the motion should execute."
    )


class StopMotionInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    acceleration: float | None = Field(
        default=None, description="Optional stopj acceleration in rad/s^2.", gt=0.0
    )


class DigitalOutputInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    output_id: int = Field(description="Standard digital output index 0-7.", ge=0, le=7)
    value: bool = Field(description="True to set high, false to set low.")
    confirm: bool = Field(
        default=False, description="Set true to confirm the IO write should execute."
    )


class RecoverInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    confirm: bool = Field(
        description="Must be true before any recovery action will run."
    )


@dataclass
class AppContext:
    config: RobotConfig
    actions: UR5eActions


def build_actions(config: RobotConfig) -> UR5eActions:
    dashboard = DashboardClient(
        config.robot_ip, port=config.dashboard_port, timeout=config.connect_timeout_s
    )
    rtde_state = RTDEStateClient(config.robot_ip, port=config.rtde_port)
    urscript = URScriptClient(
        config.robot_ip, port=config.urscript_port, timeout=config.connect_timeout_s
    )
    return UR5eActions(
        config=config, dashboard=dashboard, rtde_state=rtde_state, urscript=urscript
    )


def get_config_path() -> Path:
    configured = os.environ.get("UR5E_CONFIG")
    return Path(configured).resolve() if configured else DEFAULT_CONFIG_PATH


@asynccontextmanager
async def app_lifespan(_server: FastMCP) -> AsyncIterator[AppContext]:
    config_path = get_config_path()
    config = load_config(config_path)
    yield AppContext(config=config, actions=build_actions(config))


mcp = FastMCP(
    "ur5e_mcp",
    instructions=(
        "Guarded local MCP server for Universal Robots UR5e control. Always read status before motion. "
        "Prefer named poses over raw joint targets. Never attempt arbitrary URScript execution."
    ),
    lifespan=app_lifespan,
)


def _actions_from_context(ctx: Context[ServerSession, AppContext]) -> UR5eActions:
    return ctx.request_context.lifespan_context.actions


@mcp.tool(
    name="ur5e_get_status",
    annotations={
        "title": "Get UR5e Status",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def ur5e_get_status(ctx: Context[ServerSession, AppContext]) -> dict[str, Any]:
    """Read robot state from dashboard and RTDE.

    Returns robot mode, safety status, program state, joints, TCP pose, speed scaling,
    and digital IO state. Use this before any motion or recovery action.
    """

    return _actions_from_context(ctx).get_status()


@mcp.tool(
    name="ur5e_goto_named_pose",
    annotations={
        "title": "Move UR5e To Named Pose",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def ur5e_goto_named_pose(
    params: NamedPoseInput, ctx: Context[ServerSession, AppContext]
) -> dict[str, Any]:
    """Move the robot to a configured named joint pose.

    Prefer this tool over raw joint targets. The move is rejected if the robot is not
    in remote control, if safety status blocks motion, or if operator confirmation is required.
    """

    return _actions_from_context(ctx).goto_named_pose(
        name=params.name, confirm=params.confirm
    )


@mcp.tool(
    name="ur5e_move_joints",
    annotations={
        "title": "Move UR5e Joints",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def ur5e_move_joints(
    params: MoveJointsInput, ctx: Context[ServerSession, AppContext]
) -> dict[str, Any]:
    """Perform a guarded joint-space move.

    Use only when no suitable named pose exists. Inputs are validated against configured
    velocity and acceleration caps before a fixed-form movej command is sent.
    """

    return _actions_from_context(ctx).move_joints(
        joints=params.joints,
        velocity=params.velocity,
        acceleration=params.acceleration,
        confirm=params.confirm,
    )


@mcp.tool(
    name="ur5e_stop_motion",
    annotations={
        "title": "Stop UR5e Motion",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def ur5e_stop_motion(ctx: Context[ServerSession, AppContext]) -> dict[str, Any]:
    """Send a guarded stopj command to slow or stop joint motion."""

    return _actions_from_context(ctx).stop_motion()


@mcp.tool(
    name="ur5e_pause_program",
    annotations={
        "title": "Pause UR5e Program",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def ur5e_pause_program(ctx: Context[ServerSession, AppContext]) -> dict[str, Any]:
    """Pause the currently loaded robot program through the dashboard server."""

    return _actions_from_context(ctx).pause_program()


@mcp.tool(
    name="ur5e_resume_program",
    annotations={
        "title": "Resume UR5e Program",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def ur5e_resume_program(
    ctx: Context[ServerSession, AppContext],
) -> dict[str, Any]:
    """Resume a paused robot program through the dashboard server."""

    return _actions_from_context(ctx).resume_program()


@mcp.tool(
    name="ur5e_read_digital_io",
    annotations={
        "title": "Read UR5e Digital IO",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def ur5e_read_digital_io(
    ctx: Context[ServerSession, AppContext],
) -> dict[str, Any]:
    """Read standard digital inputs and outputs from RTDE state."""

    return _actions_from_context(ctx).read_digital_io()


@mcp.tool(
    name="ur5e_write_digital_output",
    annotations={
        "title": "Write UR5e Digital Output",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def ur5e_write_digital_output(
    params: DigitalOutputInput, ctx: Context[ServerSession, AppContext]
) -> dict[str, Any]:
    """Set a standard digital output through a fixed-form script after confirmation."""

    return _actions_from_context(ctx).write_digital_output(
        output_id=params.output_id,
        value=params.value,
        confirm=params.confirm,
    )


@mcp.tool(
    name="ur5e_recover_robot",
    annotations={
        "title": "Recover UR5e From Stop",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": True,
    },
)
async def ur5e_recover_robot(
    params: RecoverInput, ctx: Context[ServerSession, AppContext]
) -> dict[str, Any]:
    """Attempt a limited recovery flow for protective stop or power-off states.

    This tool requires confirm=true and should only be used after a human has inspected
    the cause of the stop.
    """

    return _actions_from_context(ctx).recover_robot(confirm=params.confirm)


def main() -> None:
    try:
        mcp.run()
    except GuardViolation as exc:
        raise SystemExit(str(exc)) from exc


if __name__ == "__main__":
    main()
