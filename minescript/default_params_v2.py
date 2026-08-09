from __future__ import annotations

"""Preserve FeatureExecutor.execute(feature) default-parameter behavior.

Late 2.0 report overrides intercept several feature families before the legacy executor
merges defaults. Normalizing missing params at the outer edge keeps direct/library
calls identical to GUI and dry-run calls.
"""


def install() -> None:
    from .feature_executor import FeatureExecutor

    if getattr(FeatureExecutor, "_default_params_v2_installed", False):
        return
    original_execute = FeatureExecutor.execute

    def execute(self, feature, params=None, dry_run=False):
        if params is None:
            params = self.defaults(feature)
        return original_execute(self, feature, params, dry_run)

    FeatureExecutor.execute = execute
    FeatureExecutor._default_params_v2_installed = True
