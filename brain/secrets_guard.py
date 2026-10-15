"""Finds secrets in data before it is written to a log or to the memory.

Project rule: no secrets, credentials, SIM PINs or tokens in code, logs or memory,
only references to the secret store.
"""

import re

# Key names that hold secrets. A key matches when its last part (after "_" or "-")
# is one of these words, so "bot_token" matches but "input_tokens" does not.
_SECRET_KEY = re.compile(
    r"(?i)^(?:.*[_\-.])?(password|passwort|passwd|secret|token|apikey|api_key|api-key|"
    r"pin|private_key|privatekey|credential|credentials|zugangsdaten)$"
)

# Values that look like secrets wherever they appear.
_SECRET_VALUES = (
    re.compile(r"sk-ant-[A-Za-z0-9_\-]{8,}"),  # Anthropic API key
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),  # PEM or OpenSSH private key
    re.compile(r"\b\d{6,12}:[A-Za-z0-9_\-]{30,}\b"),  # Telegram bot token
)


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
            if _SECRET_KEY.match(key_text):
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
