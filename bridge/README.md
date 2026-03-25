# UR5e MCP Bridge

This package exposes a local `stdio` MCP server for guarded `UR5e` control.

## Install

```bash
python -m pip install -e .
python -m pip install git+https://github.com/UniversalRobots/RTDE_Python_Client_Library.git@main
```

## Run

Set `UR5E_CONFIG` to a YAML config file, then start the server:

```bash
python -m ur5e_bridge.server
```

## Transport

The server uses `stdio` by default and is meant to be launched by OpenClaw as a local MCP tool server.
