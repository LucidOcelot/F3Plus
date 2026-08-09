from __future__ import annotations

"""Canonical historical-operation executor.

The 457 historical IDs remain callable for compatibility, but execution is composed
through explicit policy/services rather than import-time class mutation.
"""

from .feature_engine import (
    COMMON_FIELDS,
    MACRO_NAMES,
    FeatureExecutor as _BaseFeatureExecutor,
    FeatureResult,
)
from .version import TARGET_MINECRAFT
from . import executor_policy


class FeatureExecutor(_BaseFeatureExecutor):
    def __init__(self, minecraft_version=TARGET_MINECRAFT):
        super().__init__(minecraft_version)

    def _base_input_fields(self, feature):
        return super().input_fields(feature)

    def _base_execute(self, feature, params=None, dry_run=False):
        return super().execute(feature, params, dry_run)

    def input_fields(self, feature):
        return executor_policy.input_fields(self, self.spec(feature))

    def dry_run(self, feature):
        return executor_policy.dry_run(self, self.spec(feature))

    def execute(self, feature, params=None, dry_run=False):
        return executor_policy.execute(self, self.spec(feature), params, dry_run)


__all__ = ["FeatureExecutor", "FeatureResult", "MACRO_NAMES", "COMMON_FIELDS"]
