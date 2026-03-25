from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any, Dict


class RTDEStateError(RuntimeError):
    """Raised when RTDE state cannot be read."""


class RTDEStateClient:
    def __init__(
        self, host: str, port: int = 30004, recipe_path: str | Path | None = None
    ) -> None:
        self.host = host
        self.port = port
        self.recipe_path = (
            Path(recipe_path)
            if recipe_path
            else Path(__file__).with_name("rtde_recipe.xml")
        )

    def read_state(self) -> Dict[str, Any]:
        try:
            rtde = importlib.import_module("rtde.rtde")
            rtde_config = importlib.import_module("rtde.rtde_config")
        except ImportError as exc:
            raise RTDEStateError(
                "RTDE Python library is not installed. Install git+https://github.com/UniversalRobots/RTDE_Python_Client_Library.git@main"
            ) from exc

        conf = rtde_config.ConfigFile(str(self.recipe_path))
        output_names, output_types = conf.get_recipe("out")

        connection = rtde.RTDE(self.host, self.port)

        try:
            connection.connect()
            connection.get_controller_version()
            if not connection.send_output_setup(
                output_names, output_types, frequency=10
            ):
                raise RTDEStateError(
                    "Unable to configure RTDE output. Confirm RTDE is enabled in robot security settings."
                )
            if not connection.send_start():
                raise RTDEStateError("Unable to start RTDE synchronization.")

            state = connection.receive()
            if state is None:
                raise RTDEStateError("No RTDE state received from robot.")

            return {name: getattr(state, name) for name in output_names}
        except OSError as exc:
            raise RTDEStateError(
                f"RTDE connection failed. Check robot_ip={self.host}, port={self.port}, and RTDE availability."
            ) from exc
        finally:
            try:
                connection.send_pause()
            except Exception:
                pass
            try:
                connection.disconnect()
            except Exception:
                pass
