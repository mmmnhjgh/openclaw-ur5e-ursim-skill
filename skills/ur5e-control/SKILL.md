---
name: ur5e-control
description: Use this skill to control a Universal Robots UR5e through the local ur5e_mcp stdio server. Supports guarded status checks, named-pose moves, constrained joint moves, digital IO, and operator-confirmed recovery.
---

# UR5e Control Skill

Use this skill when the user wants to inspect or control a `UR5e` in `URSim` or on real hardware through the local `ur5e_mcp` bridge.

## Purpose

This skill keeps the model at the high-level intent layer.
The model must never generate arbitrary `URScript` for direct execution.
All robot actions must go through the `ur5e_mcp` tools.

## Default Operating Mode

- Prefer `URSim` over real hardware.
- Prefer `ur5e_get_status` before any other tool.
- Prefer `ur5e_goto_named_pose` over raw `ur5e_move_joints`.
- Keep speeds low unless the user explicitly asks for a different value and the configured limits allow it.
- Treat recovery, power, and brake operations as high-risk actions.
- If the user wants to watch the motion in URSim, keep the browser UI on `Move` or `Installation -> TCP` with `Simulation` enabled.

## Safe Workflow

1. Call `ur5e_get_status`.
2. Confirm the robot is in remote control and not in a stop or fault state.
3. If a move is needed, prefer `ur5e_goto_named_pose`.
4. Use `ur5e_move_joints` only when the requested target is not already a named pose.
5. Re-check status if a command fails.

## Available MCP Tools

- `ur5e_get_status`: Read robot mode, safety status, program state, joints, TCP pose, and digital IO.
- `ur5e_goto_named_pose`: Move to a configured named joint pose such as `home`, `approach`, or `park`.
- Demo presets may also be available, such as `demo_left`, `demo_right`, and `demo_high`.
- `ur5e_move_joints`: Perform a guarded joint-space move with validated limits.
- `ur5e_stop_motion`: Send a guarded `stopj` command.
- `ur5e_pause_program`: Pause a loaded robot program through the dashboard server.
- `ur5e_resume_program`: Resume a paused robot program through the dashboard server.
- `ur5e_read_digital_io`: Read standard digital input and output bits from RTDE state.
- `ur5e_write_digital_output`: Set a digital output through a fixed-form script.
- `ur5e_recover_robot`: Close safety popups, unlock a protective stop, and optionally power on or release brakes when confirmed.

## Hard Safety Rules

- Never emit free-form `URScript`.
- Never bypass the MCP bridge.
- Never move if `safety_status` is not motion-safe.
- Never move if the target is outside configured joint limits.
- Never move if the workspace bounds reject the current or target TCP pose.
- Never unlock protective stops repeatedly without surfacing the risk.
- Never perform high-risk actions without explicit `confirm=true` in the MCP tool call.

## Refusal Rules

Refuse and explain why when:

- the bridge reports `PROTECTIVE_STOP`, `FAULT`, `VIOLATION`, or any emergency stop state
- the robot is not in remote control mode
- no named pose exists for the requested destination
- required configuration such as `robot_ip`, `named_poses`, or bounds is missing
- the user asks for arbitrary script execution

## Good Patterns

- "Check `ur5e_get_status`, then move to `home` if the robot is safe."
- "Read digital inputs first, then set output 0 to true with confirmation."
- "Use `ur5e_recover_robot(confirm=true)` only after explaining the current stop state."

## Bad Patterns

- "Send this raw `movej(...)` script to the robot."
- "Keep unlocking the protective stop until it works."
- "Move outside the configured cell because the user asked once."

## Operator Notes

- This skill is designed for a local `stdio` MCP deployment.
- Configuration lives outside the prompt in YAML.
- The first motion in a bridge session should be operator-confirmed.
- Real hardware use still requires a clear cell, E-stop access, and line-of-sight supervision.
- In `Remote` mode, many local URSim buttons are disabled; that is normal, because OpenClaw should drive motion through MCP.
