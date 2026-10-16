"""Small validator for the subset of JSON Schema our schema files use.

A full JSON Schema library would be a foreign dependency. This module supports only
the keywords listed in SUPPORTED and refuses schemas that use anything else, so a
schema change can never be silently ignored.
"""

import json
import math
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
    "additionalProperties",
    "propertyNames",
    "minProperties",
    "items",
    "minItems",
    "maxItems",
    "enum",
    "const",
    "minimum",
    "maximum",
    "minLength",
    "maxLength",
    "format",
    "pattern",
}

_TYPES = {
    "object": lambda v: isinstance(v, dict),
    "array": lambda v: isinstance(v, list),
    "string": lambda v: isinstance(v, str),
    "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
    "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v),
    "boolean": lambda v: isinstance(v, bool),
}


class SchemaError(Exception):
    """The schema itself uses something this validator does not understand."""


def load_schema(path):
    schema = json.loads(Path(path).read_text(encoding="utf-8"))
    check_supported(schema)
    return schema


def check_supported(schema, where="$"):
    if not isinstance(schema, dict):
        raise SchemaError(f"{where}: a schema must be an object")
    unknown = set(schema) - SUPPORTED
    if unknown:
        raise SchemaError(f"{where}: unsupported keywords {sorted(unknown)}")
    if "type" in schema and schema["type"] not in _TYPES:
        raise SchemaError(f"{where}: unsupported type {schema['type']!r}")
    if "format" in schema and schema["format"] != "date-time":
        raise SchemaError(f"{where}: unsupported format {schema['format']!r}")
    for name, sub in schema.get("properties", {}).items():
        check_supported(sub, f"{where}.{name}")
    extra = schema.get("additionalProperties", True)
    if not isinstance(extra, bool):
        check_supported(extra, f"{where}.additionalProperties")
    for keyword in ("items", "propertyNames"):
        if keyword in schema:
            check_supported(schema[keyword], f"{where}.{keyword}")


def _is_datetime(value):
    try:
        parsed = datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return False
    return parsed.tzinfo is not None


def _validate_object(instance, schema, where):
    errors = []
    for name in schema.get("required", []):
        if name not in instance:
            errors.append(f"{where}.{name}: missing")
    if "minProperties" in schema and len(instance) < schema["minProperties"]:
        errors.append(f"{where}: needs at least {schema['minProperties']} entries")
    properties = schema.get("properties", {})
    extra = schema.get("additionalProperties", True)
    for name, value in instance.items():
        if not isinstance(name, str):
            errors.append(f"{where}: key {name!r} is not text")
            continue
        if "propertyNames" in schema:
            errors.extend(validate(name, schema["propertyNames"], f"{where}.<{name}>"))
        if name in properties:
            errors.extend(validate(value, properties[name], f"{where}.{name}"))
        elif extra is False:
            errors.append(f"{where}.{name}: not allowed here")
        elif isinstance(extra, dict):
            errors.extend(validate(value, extra, f"{where}.{name}"))
    return errors


def _validate_array(instance, schema, where):
    errors = []
    if "minItems" in schema and len(instance) < schema["minItems"]:
        errors.append(f"{where}: needs at least {schema['minItems']} items")
    if "maxItems" in schema and len(instance) > schema["maxItems"]:
        errors.append(f"{where}: allows at most {schema['maxItems']} items")
    if "items" in schema:
        for index, item in enumerate(instance):
            errors.extend(validate(item, schema["items"], f"{where}[{index}]"))
    return errors


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
    if isinstance(instance, str):
        if "minLength" in schema and len(instance) < schema["minLength"]:
            errors.append(f"{where}: shorter than {schema['minLength']} characters")
        if "maxLength" in schema and len(instance) > schema["maxLength"]:
            errors.append(f"{where}: longer than {schema['maxLength']} characters")
        if schema.get("format") == "date-time" and not _is_datetime(instance):
            errors.append(f"{where}: not an ISO 8601 date-time with time zone")
        if "pattern" in schema and not re.search(schema["pattern"], instance):
            errors.append(f"{where}: does not match {schema['pattern']}")
    if isinstance(instance, dict):
        errors.extend(_validate_object(instance, schema, where))
    if isinstance(instance, list):
        errors.extend(_validate_array(instance, schema, where))
    return errors
