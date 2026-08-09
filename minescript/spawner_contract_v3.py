from __future__ import annotations


def install() -> None:
    from .feature_executor import FeatureExecutor

    if getattr(FeatureExecutor, "_spawner_contract_v3_installed", False):
        return
    previous_execute = FeatureExecutor.execute

    contract = {
        "kind": "generated-world-analysis",
        "engine": "Java Anvil NBT scanner / optional exact Mojang reference generation",
        "exactness": "observed generated block-entity NBT within the scanned chunks",
        "prerequisite": "generated Java save or exact seed-regenerated vanilla chunks",
        "limitation": "Spawner mob identity is reported only when the block entity encodes it; custom/server-modified worlds can use other data.",
    }

    def execute(self, feature, params=None, dry_run=False):
        spec = self.spec(feature)
        result = previous_execute(self, spec, params, dry_run)
        if spec.top == "Seed Tools" and spec.submenu == "Spawners" and isinstance(getattr(result, "data", None), dict):
            result.data.setdefault("implementation", dict(contract))
        return result

    FeatureExecutor.execute = execute
    FeatureExecutor._spawner_contract_v3_installed = True
