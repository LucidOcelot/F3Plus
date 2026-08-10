from __future__ import annotations

"""Canonical historical-operation executor.

Historical IDs remain callable for compatibility, but every instance owns the canonical
schema/execute path. Legacy modules may still contain old ``install`` definitions for
source compatibility; a late class-level monkeypatch can no longer replace the public
executor used by the application or tests.
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
        # Bind the canonical entry points to this instance. Older compatibility modules
        # used to replace FeatureExecutor.input_fields/execute on the class. Those hooks
        # are no longer part of the runtime architecture and must not be able to alter a
        # newly-created canonical executor if a legacy module is imported by a tool/test.
        self.input_fields = self._canonical_input_fields
        self.execute = self._canonical_execute

    def _base_input_fields(self, feature):
        return super().input_fields(feature)

    def _base_defaults(self, feature):
        values = {}
        for key, _label, default, kind in self._base_input_fields(feature):
            values[key] = default[0] if kind == "choice" and isinstance(default, list) and default else default
        return values

    def _base_execute(self, feature, params=None, dry_run=False):
        values = self._base_defaults(feature)
        values.update(normalize_seed_params(params))
        return super().execute(feature, values, dry_run)

    def _canonical_input_fields(self, feature):
        spec = self.spec(feature)
        explicit = operation_fields.fields_for(spec)
        if explicit is not None:
            fields = list(explicit)
        else:
            fields = list(executor_policy.input_fields(self, spec))

        # Shared source/search policy is applied last and is idempotent. This guarantees
        # every true generated-world analyzer exposes the same World save / Seed inputs,
        # regardless of which historical schema provider supplied its task fields.
        if spec.top == "Seed Tools" and spec.name in seed_generation.SEED_REGENERATABLE:
            fields = seed_generation.add_fields(fields)
        return search_policy.add_fields(spec, fields)

    def input_fields(self, feature):
        return self._canonical_input_fields(feature)

    def dry_run(self, feature):
        return executor_policy.dry_run(self, self.spec(feature))

    def _canonical_execute(self, feature, params=None, dry_run=False):
        return executor_policy.execute(self, self.spec(feature), normalize_seed_params(params), dry_run)

    def execute(self, feature, params=None, dry_run=False):
        return self._canonical_execute(feature, params, dry_run)


__all__ = ["FeatureExecutor", "FeatureResult", "MACRO_NAMES", "COMMON_FIELDS"]
