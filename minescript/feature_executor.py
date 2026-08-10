from __future__ import annotations

"""Canonical historical-operation executor.

The historical IDs remain callable for compatibility, but execution is composed
through explicit policy/services rather than import-time class mutation. Parameter
schemas prefer operation-specific definitions so a broad category fallback never leaks
irrelevant fields into a canonical workbench.
"""

from .feature_engine import (
    COMMON_FIELDS,
    MACRO_NAMES,
    FeatureExecutor as _BaseFeatureExecutor,
    FeatureResult,
)
from .version import TARGET_MINECRAFT
from . import executor_policy, operation_fields, search_policy, seed_generation
from .seed_text import normalize_seed_params


class FeatureExecutor(_BaseFeatureExecutor):
    def __init__(self, minecraft_version=TARGET_MINECRAFT):
        super().__init__(minecraft_version)

    def _base_input_fields(self, feature):
        return super().input_fields(feature)

    def _base_defaults(self, feature):
        values = {}
        for key, _label, default, kind in self._base_input_fields(feature):
            values[key] = default[0] if kind == "choice" and isinstance(default, list) and default else default
        return values

    def _base_execute(self, feature, params=None, dry_run=False):
        # The compatibility engine historically reads broad category fields before it
        # knows which legacy operation is running. Keep those defaults internal so the
        # user-facing schema can expose only values that actually affect the operation.
        values = self._base_defaults(feature)
        values.update(normalize_seed_params(params))
        return super().execute(feature, values, dry_run)

    def input_fields(self, feature):
        spec = self.spec(feature)
        explicit = operation_fields.fields_for(spec)
        if explicit is not None:
            fields = list(explicit)
            # Explicit schemas describe operation inputs; shared world-generation and
            # expanding-search policy is composed afterward so specializing a form can
            # never accidentally remove exact Mojang generation or Search Until Found.
            if spec.top == "Seed Tools" and spec.name in seed_generation.SEED_REGENERATABLE:
                fields = seed_generation.add_fields(fields)
            return search_policy.add_fields(spec, fields)
        return executor_policy.input_fields(self, spec)

    def dry_run(self, feature):
        return executor_policy.dry_run(self, self.spec(feature))

    def execute(self, feature, params=None, dry_run=False):
        return executor_policy.execute(self, self.spec(feature), normalize_seed_params(params), dry_run)


__all__ = ["FeatureExecutor", "FeatureResult", "MACRO_NAMES", "COMMON_FIELDS"]
