"""
API key + credit tracking system.
JSON-backed with file locking and corruption recovery.
"""

import fcntl
import json
import os
import secrets
import shutil
import time
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
KEYS_FILE = DATA_DIR / "keys.json"
TOKENS_FILE = DATA_DIR / "tokens.json"

FREE_DAILY_LIMIT = 10
MAX_KEYS = 5000  # safety valve against key farming


def _ensure_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _load_json(path: Path) -> dict:
    """Load a JSON file with shared lock and corruption recovery."""
    _ensure_dir()
    if not path.exists():
        path.write_text("{}")
        return {}
    try:
        with open(path, "r") as f:
            fcntl.flock(f, fcntl.LOCK_SH)
            try:
                return json.load(f)
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)
    except (json.JSONDecodeError, ValueError):
        # Try backup
        backup = path.with_suffix(".json.bak")
        if backup.exists():
            try:
                data = json.loads(backup.read_text())
                # Restore from backup
                path.write_text(json.dumps(data, indent=2))
                return data
            except (json.JSONDecodeError, ValueError):
                pass
        # Last resort: preserve corrupted file, start fresh
        corrupted = path.with_suffix(".json.corrupted")
        shutil.copy2(path, corrupted)
        path.write_text("{}")
        return {}


def _save_json(path: Path, data: dict):
    """Save a JSON file with exclusive lock and backup."""
    _ensure_dir()
    # Write backup first
    if path.exists():
        backup = path.with_suffix(".json.bak")
        shutil.copy2(path, backup)
    with open(path, "w") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            json.dump(data, f, indent=2)
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


def _with_keys(fn):
    """Load keys, apply mutation function, save. Atomic."""
    keys = _load_json(KEYS_FILE)
    result = fn(keys)
    _save_json(KEYS_FILE, keys)
    return result


def generate_key() -> tuple[str | None, dict]:
    """Generate a new API key with free tier credits."""
    keys = _load_json(KEYS_FILE)
    if len(keys) >= MAX_KEYS:
        return None, {}
    key = f"sk-{secrets.token_hex(16)}"
    record = {
        "created": int(time.time()),
        "credits": 0,
        "free_calls_today": 0,
        "free_calls_date": _today(),
        "total_calls": 0,
        "tier": "free",
    }
    keys[key] = record
    _save_json(KEYS_FILE, keys)
    return key, record


def verify_key(key: str) -> dict | None:
    """Verify an API key and return the record, or None if invalid."""
    keys = _load_json(KEYS_FILE)
    return keys.get(key)


def can_call(key: str) -> tuple[bool, str]:
    """Check if a key has remaining calls. Returns (allowed, reason)."""
    keys = _load_json(KEYS_FILE)
    record = keys.get(key)
    if record is None:
        return False, "Invalid API key."

    # Reset free daily counter if new day
    if record.get("free_calls_date") != _today():
        record["free_calls_today"] = 0
        record["free_calls_date"] = _today()
        keys[key] = record
        _save_json(KEYS_FILE, keys)

    # Paid credits first
    if record.get("credits", 0) > 0:
        return True, "paid"

    # Free tier
    if record.get("free_calls_today", 0) < FREE_DAILY_LIMIT:
        return True, "free"

    # Out of calls
    return False, f"Free tier exhausted ({FREE_DAILY_LIMIT}/day). Use buy_credits() to purchase more."


def record_call(key: str, tool_name: str) -> dict:
    """Record a tool call against a key. Deduct credit or increment free counter."""
    keys = _load_json(KEYS_FILE)
    record = keys.get(key)
    if record is None:
        return {}

    record["total_calls"] = record.get("total_calls", 0) + 1

    if record.get("credits", 0) > 0:
        record["credits"] -= 1
        is_free = False
        cost = 0.10
    else:
        record["free_calls_today"] = record.get("free_calls_today", 0) + 1
        is_free = True
        cost = 0.00

    keys[key] = record
    _save_json(KEYS_FILE, keys)

    # Append to call log
    append_call_log(key, tool_name, cost=cost, free_tier=is_free, response_ms=0)

    return record


def add_credits(key: str, amount: int) -> dict | None:
    """Add credits to a key (called after Stripe webhook)."""
    keys = _load_json(KEYS_FILE)
    record = keys.get(key)
    if record is None:
        return None
    record["credits"] = record.get("credits", 0) + amount
    record["tier"] = "paid"
    keys[key] = record
    _save_json(KEYS_FILE, keys)
    return record


def get_usage(key: str) -> dict | None:
    """Get usage stats for a key."""
    keys = _load_json(KEYS_FILE)
    record = keys.get(key)
    if record is None:
        return None
    remaining_free = max(0, FREE_DAILY_LIMIT - record.get("free_calls_today", 0))
    return {
        "credits": record.get("credits", 0),
        "free_calls_remaining_today": remaining_free,
        "total_calls": record.get("total_calls", 0),
        "tier": record.get("tier", "free"),
    }


# --- Checkout token management ---

def create_checkout_token(api_key: str, credits: int) -> str:
    """Create a short-lived token for Stripe checkout."""
    token = secrets.token_hex(16)
    tokens = _load_json(TOKENS_FILE)

    # Clean expired tokens
    now = int(time.time())
    tokens = {k: v for k, v in tokens.items() if v.get("expires", 0) > now}

    tokens[token] = {
        "api_key": api_key,
        "credits": credits,
        "created": now,
        "expires": now + 3600,
    }
    _save_json(TOKENS_FILE, tokens)
    return token


def resolve_checkout_token(token: str) -> tuple[str, int] | None:
    """Look up and consume a checkout token. One-time use."""
    tokens = _load_json(TOKENS_FILE)

    # Clean expired
    now = int(time.time())
    tokens = {k: v for k, v in tokens.items() if v.get("expires", 0) > now}

    record = tokens.get(token)
    if record is None:
        _save_json(TOKENS_FILE, tokens)
        return None

    api_key = record["api_key"]
    credits = record["credits"]
    del tokens[token]
    _save_json(TOKENS_FILE, tokens)
    return api_key, credits


def _today() -> str:
    return time.strftime("%Y-%m-%d")


# --- Call logging ---

import datetime

CALLS_FILE = DATA_DIR / "calls.json"


def _load_calls() -> list:
    """Load the call log (a JSON array)."""
    _ensure_dir()
    if not CALLS_FILE.exists():
        CALLS_FILE.write_text("[]")
        return []
    try:
        with open(CALLS_FILE, "r") as f:
            fcntl.flock(f, fcntl.LOCK_SH)
            try:
                data = json.load(f)
                if not isinstance(data, list):
                    return []
                return data
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)
    except (json.JSONDecodeError, ValueError):
        CALLS_FILE.write_text("[]")
        return []


def _save_calls(data: list):
    """Save the call log with exclusive lock."""
    _ensure_dir()
    with open(CALLS_FILE, "w") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            json.dump(data, f, indent=2)
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


def append_call_log(key: str, tool_name: str, cost: float, free_tier: bool, response_ms: int):
    """Append a call entry to calls.json, keeping last 1000 entries."""
    entry = {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "key_prefix": key[:12] + "...",
        "tool": tool_name,
        "cost": cost,
        "free_tier": free_tier,
        "response_ms": response_ms,
    }
    calls = _load_calls()
    calls.append(entry)
    if len(calls) > 1000:
        calls = calls[-1000:]
    _save_calls(calls)


def get_audit_log(hours: int = 24) -> dict:
    """Return recent call log entries with summary stats."""
    calls = _load_calls()
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(hours=hours)
    cutoff_str = cutoff.isoformat() + "Z"

    recent = [c for c in calls if c.get("timestamp", "") >= cutoff_str]

    total_cost = sum(c.get("cost", 0) for c in recent)
    free_count = sum(1 for c in recent if c.get("free_tier", False))
    paid_count = len(recent) - free_count
    tools_used = {}
    for c in recent:
        t = c.get("tool", "unknown")
        tools_used[t] = tools_used.get(t, 0) + 1

    return {
        "period_hours": hours,
        "total_calls": len(recent),
        "free_calls": free_count,
        "paid_calls": paid_count,
        "total_cost": round(total_cost, 2),
        "tools_used": tools_used,
        "entries": recent[-100:],
    }
