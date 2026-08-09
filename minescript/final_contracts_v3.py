from __future__ import annotations

"""Guarantee that late UI/semantic view transforms cannot discard catalog contracts."""


def install() -> None:
    from dataclasses import asdict

    from .catalog_integrity import contract_for
    from .feature_executor import FeatureExecutor

    if getattr(FeatureExecutor, "_final_contracts_v3_installed", False):
        return
    previous_execute = FeatureExecutor.execute

    def execute(self, feature, params=None, dry_run=False):
        spec = self.spec(feature)
        result = previous_execute(self, spec, params, dry_run)
        data = getattr(result, "data", None)
        if isinstance(data, dict) and not isinstance(data.get("implementation"), dict):
            if "implementation" in data:
                data["implementation_detail"] = data["implementation"]
            data["implementation"] = asdict(contract_for(spec))
        return result

    FeatureExecutor.execute = execute
    FeatureExecutor._final_contracts_v3_installed = True
