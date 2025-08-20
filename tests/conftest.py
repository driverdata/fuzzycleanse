"""Pytest configuration to ensure project root importability."""

import sys
from pathlib import Path

# Add the project root to ``sys.path`` so tests can import ``app`` directly.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

