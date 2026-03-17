"""
Simple API key + credit tracking system.
Keys and balances stored in a JSON file. Good enough for first 50 customers.
"""

import json
import os
import secrets
import time
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
KEYS_FILE = DATA_DIR / "keys.json"
TOKENS_FILE = DATA_DIR / "tokens.json"

FREE_DAILY_LIMIT = 10


def _load_keys() -> dict:
    if not KEYS_FILE.exists():
        KEYS_FILE.parent.mkdir(parents=True, exist_ok=True)
        KEYS_FILE.write_text("{}")
        return {}
    return json.loads(KEYS_FILE.read_text())


def _save_keys(keys: dict):
    KEYS_FILE.parent.mkdir(parents=True, exist_ok=True)
    KEYS_FILE.write_text(json.dumps(keys, indent=2))


def _load_tokens() -> dict:
    if not TOKENS_FILE.exists():
        TOKENS_FILE.parent.mkdir(parents=True, exist_ok=True)
        TOKENS_FILE.write_text("{}")
        return {}
    return json.loads(TOKENS_FILE.read_text())


def _save_tokens(tokens: dict):
    TOKENS_FILE.parent.mkdir(parents=True, exist_ok=True)
    TOKENS_FILE.write_text(json.dumps(tokens, indent=2))


def generate_key() -> tuple[str, dict]:
    """Generate a new API key with free tier credits."""
    key = f"sk-{secrets.token_hex(16)}"
    record = {
        "created": int(time.time()),
        "credits": 0,
        "free_calls_today": 0,
        "free_calls_date": _today(),
        "total_calls": 0,
        "tier": "free",
    }
    keys = _load_keys()
    keys[key] = record
    _save_keys(keys)
    return key, record


def verify_key(key: str) -> dict | None:
    """Verify an API key and return the record, or None if invalid."""
    keys = _load_keys()
    return keys.get(key)


def can_call(key: str) -> tuple[bool, str]:
    """Check if a key has remaining calls. Returns (allowed, reason)."""
    keys = _load_keys()
    record = keys.get(key)
    if record is None:
        return False, "Invalid API key."

    # Reset free daily counter if new day
    if record.get("free_calls_date") != _today():
        record["free_calls_today"] = 0
        record["free_calls_date"] = _today()
        keys[key] = record
        _save_keys(keys)

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
    keys = _load_keys()
    record = keys.get(key)
    if record is None:
        return {}

    record["total_calls"] = record.get("total_calls", 0) + 1

    if record.get("credits", 0) > 0:
        record["credits"] -= 1
    else:
        record["free_calls_today"] = record.get("free_calls_today", 0) + 1

    keys[key] = record
    _save_keys(keys)
    return record


def add_credits(key: str, amount: int) -> dict | None:
    """Add credits to a key (called after Stripe webhook or manual top-up)."""
    keys = _load_keys()
    record = keys.get(key)
    if record is None:
        return None
    record["credits"] = record.get("credits", 0) + amount
    record["tier"] = "paid"
    keys[key] = record
    _save_keys(keys)
    return record


def get_usage(key: str) -> dict | None:
    """Get usage stats for a key."""
    keys = _load_keys()
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
    """Create a short-lived token that maps to an API key for checkout.
    The token is passed to Stripe as client_reference_id so the raw
    API key never appears in URLs or Stripe metadata."""
    token = secrets.token_hex(16)
    tokens = _load_tokens()

    # Clean expired tokens while we're here
    now = int(time.time())
    tokens = {k: v for k, v in tokens.items() if v.get("expires", 0) > now}

    tokens[token] = {
        "api_key": api_key,
        "credits": credits,
        "created": now,
        "expires": now + 3600,  # 1 hour expiry
    }
    _save_tokens(tokens)
    return token


def resolve_checkout_token(token: str) -> tuple[str, int] | None:
    """Look up a checkout token. Returns (api_key, credits) or None.
    Deletes the token after use (one-time redemption)."""
    tokens = _load_tokens()
    record = tokens.get(token)
    if record is None:
        return None
    if record.get("expires", 0) < int(time.time()):
        del tokens[token]
        _save_tokens(tokens)
        return None
    api_key = record["api_key"]
    credits = record["credits"]
    del tokens[token]
    _save_tokens(tokens)
    return api_key, credits


def _today() -> str:
    return time.strftime("%Y-%m-%d")
