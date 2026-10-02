"""Settings shared by agent.py and console.py."""
import os
import sys
from pathlib import Path

HOST = "127.0.0.1"
PORT = int(os.getenv("BROWSER_AGENT_PORT", "8765"))

# Edge ships with Windows 11, so the default needs no browser download.
# BROWSER_CHANNEL= (empty) uses Playwright's bundled Chromium instead.
CHANNEL = os.getenv("BROWSER_CHANNEL", "msedge")


def _data_dir() -> Path:
    if os.getenv("BROWSER_AGENT_HOME"):
        return Path(os.environ["BROWSER_AGENT_HOME"])
    if sys.platform == "win32":
        return Path(os.environ["LOCALAPPDATA"]) / "BrowserAgent"
    return Path.home() / ".browser-agent"


DATA_DIR = _data_dir()
DATA_DIR.mkdir(parents=True, exist_ok=True)
TOKEN_FILE = DATA_DIR / "agent.token"
PROFILE_DIR = DATA_DIR / "profile"
SHOTS_DIR = DATA_DIR / "shots"
LOG_FILE = DATA_DIR / "agent.log"
