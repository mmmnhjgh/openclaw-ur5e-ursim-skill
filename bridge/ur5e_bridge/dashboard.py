from __future__ import annotations

import socket


class DashboardError(RuntimeError):
    """Raised when the dashboard server rejects or cannot process a command."""


class DashboardClient:
    def __init__(self, host: str, port: int = 29999, timeout: float = 2.0) -> None:
        self.host = host
        self.port = port
        self.timeout = timeout

    def send_command(self, command: str) -> str:
        try:
            with socket.create_connection(
                (self.host, self.port), timeout=self.timeout
            ) as conn:
                conn.recv(4096)
                conn.sendall((command.strip() + "\n").encode("utf-8"))
                return conn.recv(4096).decode("utf-8", errors="replace").strip()
        except OSError as exc:
            raise DashboardError(
                f"Dashboard connection failed. Check robot_ip={self.host}, port={self.port}, and Remote Control mode."
            ) from exc

    def _value_command(self, command: str) -> str:
        response = self.send_command(command)
        return response.split(":", 1)[1].strip() if ":" in response else response

    def robot_mode(self) -> str:
        return self._value_command("robotmode")

    def safety_status(self) -> str:
        return self._value_command("safetystatus")

    def program_state(self) -> str:
        return self.send_command("programState")

    def running(self) -> bool:
        return self.send_command("running").lower().endswith("true")

    def is_remote_control(self) -> bool:
        return self.send_command("is in remote control").strip().lower() == "true"

    def power_on(self) -> str:
        return self.send_command("power on")

    def brake_release(self) -> str:
        return self.send_command("brake release")

    def play(self) -> str:
        return self.send_command("play")

    def stop(self) -> str:
        return self.send_command("stop")

    def pause(self) -> str:
        return self.send_command("pause")

    def unlock_protective_stop(self) -> str:
        return self.send_command("unlock protective stop")

    def close_safety_popup(self) -> str:
        return self.send_command("close safety popup")
