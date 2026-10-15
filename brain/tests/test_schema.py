"""Tests for the small JSON-Schema validator."""

import pytest

from brain.eventlog import DEFAULT_SCHEMA
from brain.schema import SchemaError, check_supported, load_schema, validate


def test_the_event_schema_uses_only_supported_keywords():
    schema = load_schema(DEFAULT_SCHEMA)
    assert schema["$id"] == "event/1.1"


def test_unknown_keywords_are_refused():
    with pytest.raises(SchemaError, match="additionalProperties"):
        check_supported({"type": "object", "additionalProperties": False})
    with pytest.raises(SchemaError):
        check_supported({"properties": {"x": {"type": "string", "maxLength": 3}}})
    with pytest.raises(SchemaError):
        check_supported({"format": "email"})


@pytest.mark.parametrize(
    ("schema", "value", "valid"),
    [
        ({"type": "integer"}, 3, True),
        ({"type": "integer"}, True, False),
        ({"type": "number"}, 2.5, True),
        ({"type": "boolean"}, 0, False),
        ({"enum": ["a", "b"]}, "c", False),
        ({"const": "x"}, "x", True),
        ({"minimum": 0}, -1, False),
        ({"maximum": 1}, 1, True),
        ({"pattern": "^[0-9a-f]{4}$"}, "beef", True),
        ({"pattern": "^[0-9a-f]{4}$"}, "BEEF", False),
        ({"format": "date-time"}, "2026-10-15T12:00:00.000Z", True),
        ({"format": "date-time"}, "2026-10-15T12:00:00", False),
        ({"format": "date-time"}, "gestern", False),
        ({"type": "object", "required": ["a"]}, {}, False),
        ({"type": "object", "properties": {"a": {"type": "string"}}}, {"a": 1}, False),
    ],
)
def test_validate(schema, value, valid):
    assert (validate(value, schema) == []) is valid
