from __future__ import annotations

"""User-facing result sanitation.

The executor may retain technical metadata for library callers and debugging.  The
presentation layer recursively removes private/internal keys before displaying a result.
This module has no installer and never mutates the application or executor.
"""


_HIDDEN_PRESENTATION_KEYS = {
    "implementation",
    "operation",
    "display_name",
    "mc_enum",
    "bundled_newest_enum",
}


def _presentation_data(value):
    if isinstance(value, dict):
        out = {}
        for key, child in value.items():
            text = str(key)
            if text.startswith("_") or text in _HIDDEN_PRESENTATION_KEYS:
                continue
            out[key] = _presentation_data(child)
        return out
    if isinstance(value, list):
        return [_presentation_data(child) for child in value]
    if isinstance(value, tuple):
        return tuple(_presentation_data(child) for child in value)
    return value


__all__ = ["_presentation_data"]
