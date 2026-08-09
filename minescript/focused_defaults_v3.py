from __future__ import annotations

"""Supply engine defaults that focused 2.x forms intentionally do not show."""


def install() -> None:
    from .feature_executor import FeatureExecutor

    if getattr(FeatureExecutor, "_focused_defaults_v3_installed", False):
        return
    previous_execute = FeatureExecutor.execute

    def execute(self, feature, params=None, dry_run=False):
        spec = self.spec(feature)
        values = dict(params or {})
        if spec.top == "Calculators" and spec.submenu == "Build":
            for key, value in {"width": 16, "length": 20, "height": 8, "spacing": 4, "sag": 4.0}.items():
                values.setdefault(key, value)
        elif spec.top == "Calculators" and spec.submenu == "Shapes":
            for key, value in {"radius": 8, "height": 12, "secondary": 5}.items():
                values.setdefault(key, value)
        elif spec.top == "Calculators" and spec.submenu == "Farm":
            for key, value in {"units": 64, "hours": 1.0, "spacing": 4}.items():
                values.setdefault(key, value)
        return previous_execute(self, spec, values, dry_run)

    FeatureExecutor.execute = execute
    FeatureExecutor._focused_defaults_v3_installed = True
