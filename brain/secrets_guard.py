"""Finds secrets in data before it is written to a log or to the memory.

Project rule: no secrets, credentials, SIM PINs or tokens in code, logs or memory,
only references to the secret store.

Two checks:
- Key names: a key whose last word is a secret word ("password", "token", "pin", ...)
  holding text or a structure. camelCase is split first, so "accessToken" counts.
  Numbers are allowed, so GPIO pins like {"pin": 16} can still be logged.
- Values: well-known key formats (Anthropic, OpenAI, GitHub, Slack, AWS, Telegram,
  private keys, HTTP auth headers). Keys without a fixed format (e.g. some EU
  providers) are only caught by their key name.
False alarms are preferred to leaks: a harmless key like "next_page_token" must be renamed.
"""

import re

_SECRET_WORDS = {
    "password",
    "passwort",
    "passwd",
    "passphrase",
    "secret",
    "token",
    "apikey",
    "pin",
    "privatekey",
    "credential",
    "credentials",
    "zugangsdaten",
    "authorization",
}

_CAMEL = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")
_SPLIT = re.compile(r"[_\-.\s]+")

# Values that look like secrets wherever they appear.
_SECRET_VALUES = (
    re.compile(r"sk-ant-[A-Za-z0-9_\-]{8,}"),  # Anthropic API key
    re.compile(r"\bsk-[A-Za-z0-9_\-]{20,}"),  # OpenAI-style API key
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}"),  # GitHub token
    re.compile(r"\bxox[abprs]-[A-Za-z0-9\-]{10,}"),  # Slack token
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),  # AWS access key id
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),  # PEM or OpenSSH private key
    re.compile(r"\b\d{6,12}:[A-Za-z0-9_\-]{30,}\b"),  # Telegram bot token
    re.compile(r"(?i)\b(bearer|basic)\s+[A-Za-z0-9._~+/\-]{16,}=*"),  # HTTP Authorization value
)


def _is_secret_key(key):
    words = [word.lower() for word in _SPLIT.split(_CAMEL.sub("_", key)) if word]
    if not words:
        return False
    last = words[-1]
    last_two = "".join(words[-2:])
    return last in _SECRET_WORDS or last_two in _SECRET_WORDS


def find_secret_in_text(text):
    """Return a short description if the text contains a secret-looking value, else None."""
    for pattern in _SECRET_VALUES:
        if pattern.search(text):
            return f"value matches {pattern.pattern[:24]}…"
    return None


def find_secret(data, path="$"):
    """Walk dicts, lists and strings; return the path of the first secret found, else None."""
    if isinstance(data, dict):
        for key, value in data.items():
            key_text = str(key)
            holds_data = isinstance(value, (str, bytes, dict, list, tuple))
            if holds_data and _is_secret_key(key_text):
                return f"{path}.{key_text}: key name"
            found = find_secret(value, f"{path}.{key_text}")
            if found:
                return found
    elif isinstance(data, (list, tuple)):
        for index, value in enumerate(data):
            found = find_secret(value, f"{path}[{index}]")
            if found:
                return found
    elif isinstance(data, str):
        found = find_secret_in_text(data)
        if found:
            return f"{path}: {found}"
    return None
