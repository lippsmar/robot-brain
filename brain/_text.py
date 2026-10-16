"""Cleaning foreign text (web pages, model answers) before it is shown, spoken or stored.

Whole terminal escape sequences (ESC [ … letter) go first, so no "[31m" is left behind, then
the remaining control characters. Tab and newline stay.
"""

import re

_ESCAPE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]|\x9b[0-?]*[ -/]*[@-~]")
_CONTROL = re.compile(r"[\x00-\x08\x0b-\x1f\x7f-\x9f]")


def clean(text):
    return _CONTROL.sub("", _ESCAPE.sub("", text or ""))
