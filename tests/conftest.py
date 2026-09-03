"""Pytest configuration: ensure the project root is importable and provide
sensible default environment variables so modules that read env vars at import
time don't crash.
"""
import os
import sys
from pathlib import Path

# Project root on sys.path so top-level modules (conversation_storage, etc.)
# are importable when pytest is run from anywhere.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Provide harmless defaults for env vars read at import time. Individual tests
# may override these via monkeypatch.
os.environ.setdefault("HASS_API_URL", "ha.local:8123")
os.environ.setdefault("HASS_TOKEN", "fake-token")
os.environ.setdefault("OPENROUTER_API_KEY", "fake-key")
os.environ.setdefault("LOG_DIR", str(ROOT / "logs"))
