from __future__ import annotations

"""Expose the actual observation form for Java LCG recovery tools."""


def install() -> None:
    from .feature_executor import FeatureExecutor
    from .rng_recovery import parse_integer, split_java_next_long

    if getattr(FeatureExecutor, "_rng_recovery_semantics_v3_installed", False):
        return
    previous_execute = FeatureExecutor.execute

    def execute(self, feature, params=None, dry_run=False):
        spec = self.spec(feature)
        result = previous_execute(self, spec, params, dry_run)
        data = getattr(result, "data", None)
        if not isinstance(data, dict) or spec.top != "RNG Tools" or spec.submenu != "RNG Recovery":
            return result
        values = self.defaults(spec)
        values.update(params or {})
        if spec.name == "Java LCG State Recovery - 2 nextInt":
            data["observation_format"] = "two consecutive unbounded java.util.Random.nextInt() outputs"
            data["observed_next_ints"] = [parse_integer(values.get("first", 0)), parse_integer(values.get("second", 0))]
            data["observations_consumed"] = 2
        elif spec.name == "Java LCG State Recovery - nextLong":
            observed = parse_integer(values.get("observed_long", 0))
            first, second = split_java_next_long(observed)
            data["observation_format"] = "one java.util.Random.nextLong() output"
            data["observed_next_long"] = observed
            data["derived_next32_pair"] = [first, second]
            data["observations_consumed"] = 1
        return result

    FeatureExecutor.execute = execute
    FeatureExecutor._rng_recovery_semantics_v3_installed = True
