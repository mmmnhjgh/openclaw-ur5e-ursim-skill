from __future__ import annotations

import sys
from pathlib import Path


BRIDGE_PATH = Path(__file__).resolve().parents[1] / "bridge"

if str(BRIDGE_PATH) not in sys.path:
    sys.path.insert(0, str(BRIDGE_PATH))
