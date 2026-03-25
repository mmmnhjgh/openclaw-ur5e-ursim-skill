# UR5e OpenClaw Skill

This folder contains a local-first `UR5e` control skill for OpenClaw plus the configuration expected by the companion `ur5e_mcp` bridge.

## What this stack does

- constrains the model to guarded robot actions
- routes all robot control through a local MCP server
- supports `URSim` first, then real hardware

## Prerequisites

- Python 3.10+
- local access to the `bridge` package in this workspace
- a reachable `URSim` or `UR5e`
- remote control enabled on the robot
- RTDE enabled in robot security settings

## Files

- `SKILL.md`: model-facing behavior and safety rules
- `config.example.yaml`: copy and edit for your robot or simulator
- `config.ursim.yaml`: ready-to-use local URSim config
- `safety_checklist.md`: pre-run and recovery checklist
- `OPENCLAW_QUICKSTART.md`: exact OpenClaw and browser animation steps

## Quick start with URSim

1. Start `URSim` and expose at least ports `29999`, `30002`, and `30004`.
2. Copy `skills/ur5e-control/config.example.yaml` to a real config file and update `robot_ip`.
3. Install the bridge dependencies:

```bash
cd bridge
python -m pip install -e .
python -m pip install git+https://github.com/UniversalRobots/RTDE_Python_Client_Library.git@main
```

4. Launch the MCP bridge with the config path in `UR5E_CONFIG`.

PowerShell:

```powershell
$env:UR5E_CONFIG = "C:\Users\kongb\Desktop\优傲机械臂，UR5e\skills\ur5e-control\config.example.yaml"
python -m ur5e_bridge.server
```

Or use the ready-made launcher in `bridge/start_ur5e_mcp.ps1`, which points to `skills/ur5e-control/config.ursim.yaml`.

5. Register the server in OpenClaw using `stdio`.

Suggested command:

```text
python -m ur5e_bridge.server
```

## Watch the web animation while OpenClaw controls URSim

1. Open the URSim UI in a browser:

```text
http://localhost:6080/vnc.html?host=localhost&port=6080
```

2. Keep the robot in `Remote` mode.
3. Turn on the bottom-right `Simulation` toggle.
4. Switch the URSim UI to `Move` or `Installation -> TCP` so the robot model stays visible.
5. Send motion commands from OpenClaw through the MCP server.

When the robot is in `Remote` mode, many local buttons are intentionally disabled. That is expected. The robot should be moved by MCP tools such as `ur5e_goto_named_pose` or `ur5e_move_joints`, and the browser view will show the motion.

## Recommended first MCP calls

1. `ur5e_get_status`
2. `ur5e_goto_named_pose(name="home", confirm=true)`
3. `ur5e_stop_motion()`

## Verified URSim flow

- `Dashboard Server` reachable on `127.0.0.1:29999`
- `RTDE` reachable on `127.0.0.1:30004`
- `URScript` socket reachable on `127.0.0.1:30002`
- status read works through the bridge
- a guarded `goto_named_pose("home")` changes `actual_q`, so URSim motion is visible in the web UI when `Simulation` is on
- a guarded `goto_named_pose("park")` reaches the target joint pose in URSim

## Notes

- The bridge sends only fixed-form motion or IO scripts after validation.
- `ur5e_pause_program` and `ur5e_resume_program` are for loaded robot programs, not arbitrary socket scripts.
- For real hardware, review `skills/ur5e-control/safety_checklist.md` before any motion.
