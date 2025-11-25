# metta_adapter.py
import os
import time
import json
import logging
from typing import Optional

import requests

logger = logging.getLogger("metta_adapter")
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(ch)

METTA_URL = os.getenv("METTA_URL", "").strip()  # e.g. "http://127.0.0.1:9000/metta"
PYT_API_CANDIDATES = ["hyperon", "metta"]  # try import in this order

# Try to import a Python MeTTa API (Hyperon / metta) if available
_metta_py = None
for pkg in PYT_API_CANDIDATES:
    try:
        _metta_py = __import__(pkg)
        logger.info(f"Using Python MeTTa API from package '{pkg}'")
        break
    except Exception:
        _metta_py = None

def query_metta_via_python(query: str, timeout: float = 5.0) -> str:
    """Call local Python MeTTa API. Adapt to the actual API available in your install."""
    if _metta_py is None:
        raise RuntimeError("No Python MeTTa API available")

    # NOTE: different MeTTa Python bindings have different APIs.
    # Below are two common patterns; adjust if your installed package exposes another entry.
    # 1) hyperon/metta may provide a function like _metta_py.evaluate or metta.repl.run -> adapt here.
    # 2) If you install a specific package, replace this block with the proper call.

    # Example adaptation attempt (many installations will need you to replace this):
    try:
        if hasattr(_metta_py, "evaluate") or hasattr(_metta_py, "eval"):
            fn = getattr(_metta_py, "evaluate", getattr(_metta_py, "eval"))
            out = fn(query, timeout=timeout)
            return str(out)
        # Some libs use a `repl`/`run_script` style:
        if hasattr(_metta_py, "repl") and hasattr(_metta_py.repl, "run"):
            out = _metta_py.repl.run(query)
            return str(out)
    except Exception as e:
        logger.exception("Python MeTTa API call failed")
        raise

    raise RuntimeError("Python MeTTa API found but no compatible call pattern detected. Please adapt metta_adapter.query_metta_via_python")

def query_metta_via_http(query: str, timeout: float = 5.0, retries: int = 2) -> str:
    if not METTA_URL:
        raise RuntimeError("METTA_URL not set - cannot use HTTP MeTTa")
    payload = {"query": query}
    headers = {"Content-Type": "application/json"}
    last_exc = None
    for attempt in range(1, retries + 1):
        try:
            logger.info(f"HTTP MeTTa attempt {attempt} -> {METTA_URL}")
            r = requests.post(METTA_URL, json=payload, headers=headers, timeout=timeout)
            r.raise_for_status()
            data = r.json()
            # Expecting response like {"response":"..."} — adjust if your real MeTTa returns different shape
            if isinstance(data, dict) and "response" in data:
                return data["response"]
            # fallback: return raw JSON string
            return json.dumps(data)
        except Exception as e:
            logger.warning(f"HTTP MeTTa attempt {attempt} failed: {e}")
            last_exc = e
            time.sleep(0.5 * attempt)
    raise RuntimeError(f"All HTTP attempts failed: {last_exc}")

def query_metta(query: str, prefer: Optional[str] = None, **kwargs) -> str:
    """
    High-level method used by agents.
    prefer: 'python' | 'http' | None
    """
    logger.info(f"Querying MeTTa for: {query!r} (prefer={prefer})")
    if prefer == "python":
        return query_metta_via_python(query, **kwargs)
    if prefer == "http":
        return query_metta_via_http(query, **kwargs)

    # default behavior: python API if installed, otherwise HTTP
    if _metta_py is not None:
        try:
            return query_metta_via_python(query, **kwargs)
        except Exception as e:
            logger.warning("Python MeTTa call failed, falling back to HTTP", exc_info=True)
    return query_metta_via_http(query, **kwargs)
