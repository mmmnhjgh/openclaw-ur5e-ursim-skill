from pathlib import Path

import pytest

from ur5e_bridge.config import load_config


def test_load_config_success(tmp_path: Path) -> None:
    config_file = tmp_path / "robot.yaml"
    config_file.write_text(
        """
robot_ip: 127.0.0.1
workspace_bounds:
  x: [-0.5, 0.5]
  y: [-0.5, 0.5]
  z: [0.1, 0.8]
named_poses:
  home: [0, -1.57, 1.57, -1.57, -1.57, 0]
""".strip(),
        encoding="utf-8",
    )

    config = load_config(config_file)

    assert config.robot_ip == "127.0.0.1"
    assert config.named_poses["home"][1] == -1.57


def test_load_config_rejects_bad_named_pose(tmp_path: Path) -> None:
    config_file = tmp_path / "robot.yaml"
    config_file.write_text(
        """
robot_ip: 127.0.0.1
workspace_bounds:
  x: [-0.5, 0.5]
  y: [-0.5, 0.5]
  z: [0.1, 0.8]
named_poses:
  broken: [0, 1]
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        load_config(config_file)
