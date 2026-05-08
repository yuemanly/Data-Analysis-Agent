"""Shared singletons — import from here, never instantiate elsewhere."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from data.session import SessionManager
from LLM.llm_config_manager import get_config_manager

session_manager: SessionManager = SessionManager()
config_manager = get_config_manager()
chart_store: dict[str, str] = {}   # chart_id (hex) → full HTML string
