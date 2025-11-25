# registry_utils.py
import json
import os
from typing import Optional

_REGISTRY_PATH = os.path.join(os.path.dirname(__file__), "agents_registry.json")

def _read_registry() -> dict:
    if not os.path.exists(_REGISTRY_PATH):
        return {}
    try:
        with open(_REGISTRY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def _write_registry(data: dict) -> None:
    tmp = _REGISTRY_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, _REGISTRY_PATH)

def save_agent_address(name: str, address: str) -> None:
    data = _read_registry()
    data[name] = {"address": address}
    _write_registry(data)

def load_agent_address(name: str) -> Optional[str]:
    data = _read_registry()
    entry = data.get(name)
    if entry:
        return entry.get("address")
    return None

def list_agents() -> dict:
    return _read_registry()
