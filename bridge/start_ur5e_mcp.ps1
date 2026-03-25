$root = Split-Path -Parent $PSScriptRoot
$config = Join-Path $root "skills\ur5e-control\config.ursim.yaml"
$env:UR5E_CONFIG = $config

Write-Host "Using UR5E_CONFIG=$config"
python -m ur5e_bridge.server
