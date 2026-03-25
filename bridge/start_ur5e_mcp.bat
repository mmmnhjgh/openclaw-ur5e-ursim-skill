@echo off
set ROOT=%~dp0..
set UR5E_CONFIG=%ROOT%\skills\ur5e-control\config.ursim.yaml
echo Using UR5E_CONFIG=%UR5E_CONFIG%
python -m ur5e_bridge.server
