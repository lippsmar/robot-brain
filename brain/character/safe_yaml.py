"""Strict YAML loading for Schlaubi's own data files (profile, test questions).

- Only `yaml.SafeLoader`: no Python objects, no code.
- Duplicate keys are refused; a plain loader silently keeps the last one, which can hide a change.
- Aliases are refused; they could make a small file expand into a huge structure during checks.
- Files above a size limit, keys that are lists or mappings, and very deep nesting are refused.
"""

import yaml


class YamlError(ValueError):
    """The text is too large, not valid YAML, or uses duplicate keys or aliases."""


class _StrictLoader(yaml.SafeLoader):
    """SafeLoader that refuses duplicate keys instead of keeping the last one."""


def _construct_mapping(loader, node, deep=False):
    seen = set()
    for key_node, _ in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if isinstance(key, (list, dict, set)):
            raise YamlError(f"Schlüssel muss ein einfacher Wert sein (Zeile {key_node.start_mark.line + 1})")
        if key in seen:
            raise YamlError(f"Schlüssel doppelt: {key!r} (Zeile {key_node.start_mark.line + 1})")
        seen.add(key)
    return yaml.SafeLoader.construct_mapping(loader, node, deep=deep)


_StrictLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping)


def load_yaml(text, *, max_bytes):
    if len(text.encode("utf-8")) > max_bytes:
        raise YamlError(f"zu groß (mehr als {max_bytes} Bytes)")
    try:
        if any(isinstance(event, yaml.AliasEvent) for event in yaml.parse(text, Loader=yaml.SafeLoader)):
            raise YamlError("Verweise (YAML-Aliase) sind nicht erlaubt")
        return yaml.load(text, Loader=_StrictLoader)  # noqa: S506  _StrictLoader is a SafeLoader
    except yaml.YAMLError as error:
        raise YamlError(f"kein gültiges YAML: {error}") from error
    except RecursionError as error:
        raise YamlError("zu tief verschachtelt") from error
