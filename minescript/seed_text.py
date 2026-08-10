from __future__ import annotations

"""Human seed handling shared by world and simulator UIs.

Minecraft accepts numeric seeds and text seeds. F3+ mirrors that behavior and uses the
literal text ``F3Plus`` whenever the user leaves a seed blank.
"""

DEFAULT_SEED_TEXT = "F3Plus"


def java_string_hash(text: str) -> int:
    """Return Java String.hashCode() as a signed 32-bit integer."""
    value = 0
    for char in str(text):
        value = (31 * value + ord(char)) & 0xFFFFFFFF
    return value - 0x100000000 if value & 0x80000000 else value


def seed_number(value) -> int:
    """Resolve a Minecraft-style numeric or text seed to a deterministic integer."""
    text = str(value if value is not None else "").strip() or DEFAULT_SEED_TEXT
    try:
        return int(text, 10)
    except ValueError:
        return java_string_hash(text)


def seed_display(value) -> str:
    text = str(value if value is not None else "").strip()
    return text or DEFAULT_SEED_TEXT


def normalize_seed_params(params: dict | None) -> dict:
    """Normalize public seed fields while leaving unrelated values untouched."""
    values = dict(params or {})
    for key in ("seed", "second_seed"):
        if key in values:
            values[key] = seed_number(values.get(key))
    return values
