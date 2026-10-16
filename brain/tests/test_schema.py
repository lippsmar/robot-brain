"""Tests for the small JSON-Schema validator."""

import pytest

from brain.eventlog import DEFAULT_SCHEMA
from brain.schema import SchemaError, check_supported, load_schema, validate


def test_the_event_schema_uses_only_supported_keywords():
    schema = load_schema(DEFAULT_SCHEMA)
    assert schema["$id"] == "event/1.1"


def test_unknown_keywords_are_refused():
    with pytest.raises(SchemaError, match="oneOf"):
        check_supported({"type": "object", "oneOf": []})
    with pytest.raises(SchemaError):
        check_supported({"properties": {"x": {"type": "string", "$ref": "#/x"}}})
    with pytest.raises(SchemaError):
        check_supported({"format": "email"})


@pytest.mark.parametrize(
    "schema",
    [
        {"type": "array", "items": {"type": "string", "uniqueItems": True}},
        {"type": "object", "additionalProperties": {"type": "number", "multipleOf": 2}},
        {"type": "object", "propertyNames": {"pattern": "^a", "if": {}}},
        {"type": "object", "additionalProperties": "yes"},
    ],
)
def test_unknown_keywords_are_refused_inside_nested_schemas(schema):
    with pytest.raises(SchemaError):
        check_supported(schema)


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
        ({"type": "object", "properties": {"a": {}}, "additionalProperties": False}, {"a": 1}, True),
        ({"type": "object", "properties": {"a": {}}, "additionalProperties": False}, {"a": 1, "b": 2}, False),
        ({"type": "object", "additionalProperties": {"type": "integer"}}, {"x": 1, "y": 2}, True),
        ({"type": "object", "additionalProperties": {"type": "integer"}}, {"x": 1, "y": "2"}, False),
        ({"type": "object", "propertyNames": {"pattern": "^[a-z_]+$"}}, {"gut_so": 1}, True),
        ({"type": "object", "propertyNames": {"pattern": "^[a-z_]+$"}}, {"Böse": 1}, False),
        ({"type": "object", "minProperties": 1}, {}, False),
        ({"type": "array", "items": {"type": "string"}}, ["a", "b"], True),
        ({"type": "array", "items": {"type": "string"}}, ["a", 2], False),
        ({"type": "array"}, ("a",), False),
        ({"type": "array", "minItems": 1}, [], False),
        ({"type": "array", "maxItems": 2}, [1, 2, 3], False),
        ({"type": "string", "minLength": 2}, "a", False),
        ({"type": "string", "maxLength": 3}, "abcd", False),
        ({"type": "string", "maxLength": 3}, "äöü", True),
    ],
)
def test_validate(schema, value, valid):
    assert (validate(value, schema) == []) is valid


@pytest.mark.parametrize("value", [float("nan"), float("inf")])
def test_numbers_must_be_finite(value):
    assert validate(value, {"type": "number"}) != []
