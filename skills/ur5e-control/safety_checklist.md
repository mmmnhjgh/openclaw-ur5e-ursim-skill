# UR5e Safety Checklist

## Before connecting

- confirm the correct `robot_ip`
- confirm the robot is in `Remote Control`
- confirm `RTDE` is enabled
- confirm the cell is clear and the E-stop is reachable
- confirm the configured `tcp_offset`, `payload`, and named poses match the setup

## Before the first motion

- call `ur5e_get_status`
- verify `safety_status` is motion-safe
- verify the planned target is a configured named pose when possible
- keep speed at the configured default unless there is a reason to increase it

## If a move is rejected

- inspect the reported reason
- do not bypass the rejection with raw scripts
- fix the configuration or robot state first

## If the robot enters protective stop

- inspect the cause in PolyScope or the controller logs
- clear the physical hazard first
- only then call `ur5e_recover_robot(confirm=true)`
- if repeated protective stops occur, stop automation and investigate

## Real hardware reminder

- do not leave the robot unattended during early bring-up
- keep line-of-sight to the arm during test motions
- use low speed and empty payload until validation is complete
