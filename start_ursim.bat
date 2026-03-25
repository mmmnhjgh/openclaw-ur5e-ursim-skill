@echo off
echo Pulling latest URSim image...
docker pull universalrobots/ursim_e-series

docker rm -f ursim >nul 2>nul

echo Starting URSim container...
docker run --rm -dit --name ursim ^
  -e ROBOT_MODEL=UR5 ^
  -p 29999:29999 ^
  -p 30001:30001 ^
  -p 30002:30002 ^
  -p 30003:30003 ^
  -p 30004:30004 ^
  -p 5900:5900 ^
  -p 6080:6080 ^
  universalrobots/ursim_e-series

echo URSim started. Open: http://localhost:6080/vnc.html?host=localhost&port=6080
