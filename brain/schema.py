"""Small validator for the subset of JSON Schema our schema files use.

A full JSON Schema library would be a foreign dependency. This module supports only
the keywords listed in SUPPORTED and refuses schemas that use anything else, so a
schema change can never be silently ignored.
"""

import json
import re
from datetime import datetime
from pathlib import Path

SUPPORTED = {
    "$schema",
    "$id",
    "title",
    "description",
    "type",
    "required",
    "properties",
    "enum",
    "const",
    "minimum",
    "maximum",
    "format",
    "pattern",
}

_TYPES = {
    "object": lambda v: isinstance(v, dict),
    "string": lambda v: isinstance(v, str),
    "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
    "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
    "boolean": lambda v: isinstance(v, bool),
}


class SchemaError(Exception):
    """The schema itself uses something this validator does not understand."""


def load_schema(path):
    schema = json.loads(Path(path).read_text(encoding="utf-8"))
    check_supported(schema)
    return schema


def check_supported(schema, where="$"):
    unknown = set(schema) - SUPPORTED
    if unknown:
        raise SchemaError(f"{where}: unsupported keywords {sorted(unknown)}")
    if "type" in schema and schema["type"] not in _TYPES:
        raise SchemaError(f"{where}: unsupported type {schema['type']!r}")
    if "format" in schema and schema["format"] != "date-time":
        raise SchemaError(f"{where}: unsupported format {schema['format']!r}")
    for name, sub in schema.get("properties", {}).items():
        check_supported(sub, f"{where}.{name}")


def _is_datetime(value):
    try:
        parsed = datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return False
    return parsed.tzinfo is not None


def validate(instance, schema, where="$"):
    """Return a list of error messages; an empty list means valid."""
    errors = []
    expected = schema.get("type")
    if expected and not _TYPES[expected](instance):
        return [f"{where}: expected {expected}"]
    if "const" in schema and instance != schema["const"]:
        errors.append(f"{where}: must be {schema['const']!r}")
    if "enum" in schema and instance not in schema["enum"]:
        errors.append(f"{where}: {instance!r} is not allowed")
    if "minimum" in schema and _TYPES["number"](instance) and instance < schema["minimum"]:
        errors.append(f"{where}: below minimum {schema['minimum']}")
    if "maximum" in schema and _TYPES["number"](instance) and instance > schema["maximum"]:
        errors.append(f"{where}: above maximum {schema['maximum']}")
    if schema.get("format") == "date-time" and isinstance(instance, str) and not _is_datetime(instance):
        errors.append(f"{where}: not an ISO 8601 date-time with time zone")
    if "pattern" in schema and isinstance(instance, str) and not re.search(schema["pattern"], instance):
        errors.append(f"{where}: does not match {schema['pattern']}")
    if isinstance(instance, dict):
        for name in schema.get("required", []):
            if name not in instance:
                errors.append(f"{where}.{name}: missing")
        for name, sub in schema.get("properties", {}).items():
            if name in instance:
                errors.extend(validate(instance[name], sub, f"{where}.{name}"))
    return errors
