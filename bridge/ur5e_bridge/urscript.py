from __future__ import annotations

import socket
from typing import Iterable


class URScriptError(RuntimeError):
    """Raised when a fixed-form URScript command cannot be sent."""


class URScriptClient:
    def __init__(self, host: str, port: int = 30002, timeout: float = 2.0) -> None:
        self.host = host
        self.port = port
        self.timeout = timeout

    def send(self, script: str) -> str:
        try:
            with socket.create_connection(
                (self.host, self.port), timeout=self.timeout
            ) as conn:
                conn.sendall(script.encode("utf-8"))
        except OSError as exc:
            raise URScriptError(
                f"URScript socket connection failed. Check robot_ip={self.host}, port={self.port}, and controller reachability."
            ) from exc
        return "sent"

    def movej(
        self, joints: Iterable[float], acceleration: float, velocity: float
    ) -> str:
        joint_list = ", ".join(f"{value:.6f}" for value in joints)
        script = (
            "def openclaw_movej():\n"
            f"  movej([{joint_list}], a={acceleration:.6f}, v={velocity:.6f})\n"
            "end\n"
        )
        return self.send(script)

    def stopj(self, acceleration: float) -> str:
        script = f"def openclaw_stopj():\n  stopj({acceleration:.6f})\nend\n"
        return self.send(script)

    def set_digital_output(self, output_id: int, value: bool) -> str:
        script = (
            "sec openclaw_set_do():\n"
            f"  set_digital_out({output_id}, {'True' if value else 'False'})\n"
            "end\n"
        )
        return self.send(script)
