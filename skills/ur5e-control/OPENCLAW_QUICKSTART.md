# OpenClaw Quickstart

## Goal

Let OpenClaw control `URSim` while you watch the robot animation in the browser.

## Browser view

Open:

```text
http://localhost:6080/vnc.html?host=localhost&port=6080
```

Keep these settings:

- top-right mode: `Remote`
- bottom-left status: `Normal`
- bottom-right `Simulation`: on
- active page: `Move` or `Installation -> TCP`

## Start the local MCP bridge

PowerShell:

```powershell
cd "C:\Users\kongb\Desktop\优傲机械臂，UR5e\bridge"
.\start_ur5e_mcp.ps1
```

CMD:

```bat
cd /d "C:\Users\kongb\Desktop\优傲机械臂，UR5e\bridge"
start_ur5e_mcp.bat
```

## Register in OpenClaw

Use this local `stdio` command:

```text
python -m ur5e_bridge.server
```

Environment variable:

```text
UR5E_CONFIG=C:\Users\kongb\Desktop\优傲机械臂，UR5e\skills\ur5e-control\config.ursim.yaml
```

## Good first prompts for OpenClaw

- `Call ur5e_get_status and tell me the robot state.`
- `Move the UR5e to the named pose park with confirmation enabled.`
- `Move the UR5e between demo_left and demo_right so I can watch the browser animation.`
- `Move the UR5e to demo_high, then back to home.`

## Notes

- In `Remote` mode, many local UI buttons are disabled. That is expected.
- The robot should move from OpenClaw or MCP tools, not from the local play button.
- If motion is rejected, call `ur5e_get_status` first and check `remote_control`, `robot_mode`, and `safety_status`.

## If you switch to a real robot later

- Copy `skills/ur5e-control/config.real.example.yaml` to `skills/ur5e-control/config.real.yaml`
- Fill in the real `robot_ip`, `tcp_offset`, `payload`, `workspace_bounds`, and safe `named_poses`
- Start the bridge with that file instead of `config.ursim.yaml`
- First test only `ur5e_get_status` and a slow move to `home`
