from .version import VERSION as __version__, TARGET_MINECRAFT, STABLE_MINECRAFT

# Install concrete replacements for the legacy generic fallback families at package
# import time so CLI/tests/library callers receive the same behavior as the desktop UI.
from .qa_features import install as _install_qa_features

_install_qa_features()
del _install_qa_features

# Enforce implementation contracts across the complete original feature catalog.
from .full_catalog import install as _install_full_catalog

_install_full_catalog()
del _install_full_catalog

# Parameterize direct executor paths that historically returned canned examples.
from .catalog_direct import install as _install_catalog_direct

_install_catalog_direct()
del _install_catalog_direct

# Allow terrain/block-state analyzers to consume exact vanilla chunks regenerated
# from seed + selected Minecraft version when no generated save is supplied.
from .seed_worldgen_patch import install as _install_seed_worldgen_patch

_install_seed_worldgen_patch()
del _install_seed_worldgen_patch

# Keep direct/library FeatureExecutor construction aligned with the current F3+ target.
from .version_defaults import install as _install_version_defaults

_install_version_defaults()
del _install_version_defaults

# Correct user-facing result semantics while keeping stable catalog IDs intact.
from .result_semantics_v2 import install as _install_result_semantics_v2

_install_result_semantics_v2()
del _install_result_semantics_v2

# Apply display-only naming/documentation corrections without changing feature IDs.
from .display_metadata_v2 import install as _install_display_metadata_v2

_install_display_metadata_v2()
del _install_display_metadata_v2

# Replace ambiguous aggregate values and duplicate reports with distinct, readable
# seed/world analysis reports. Raw IDs remain available only where technically useful.
from .analysis_reports_v2 import install as _install_analysis_reports_v2

_install_analysis_reports_v2()
del _install_analysis_reports_v2

# Late report overrides intercept some features before the legacy executor merges its
# defaults. Normalize missing params at the outer edge for direct/library callers.
from .default_params_v2 import install as _install_default_params_v2

_install_default_params_v2()
del _install_default_params_v2

# Final catalog-wide semantic pass. Historical IDs remain stable, while different
# buttons now expose genuinely different jobs or explicitly labeled canonical views.
from .semantic_cleanup_v2 import install as _install_semantic_cleanup_v2

_install_semantic_cleanup_v2()
del _install_semantic_cleanup_v2

# Audit/finalize remaining shared-engine families (spawner/slime variants, guided
# setup shortcuts, probability presets, and construction-grid semantics).
from .semantic_audit_v2 import install as _install_semantic_audit_v2

_install_semantic_audit_v2()
del _install_semantic_audit_v2

# Remove the last opaque heuristic scores/raw tuples and replace them with readable
# ranking factors, explicit units, translated coordinates, and honest model limits.
from .semantic_quality_v2 import install as _install_semantic_quality_v2

_install_semantic_quality_v2()
del _install_semantic_quality_v2

# Keep waypoint lookup, sorting, and route construction as separate user operations.
from .semantic_waypoints_v2 import install as _install_semantic_waypoints_v2

_install_semantic_waypoints_v2()
del _install_semantic_waypoints_v2

# Keep Inspector/display names aligned with the final quality corrections.
from .display_quality_v2 import install as _install_display_quality_v2

_install_display_quality_v2()
del _install_display_quality_v2

# Spawner tools inspect generated NBT for the actual spawned mob and expose filters
# instead of treating every mob-spawner block as the same result.
from .spawner_v3 import install as _install_spawner_v3

_install_spawner_v3()
del _install_spawner_v3

# The final spawner layer still participates in the catalog integrity contract used by
# dry-run regression tests and technical details.
from .spawner_contract_v3 import install as _install_spawner_contract_v3

_install_spawner_contract_v3()
del _install_spawner_contract_v3

# Expose the actual observation forms of the Java LCG recovery tools so a pair of
# nextInt observations and one nextLong observation cannot collapse to the same report.
from .rng_recovery_semantics_v3 import install as _install_rng_recovery_semantics_v3

_install_rng_recovery_semantics_v3()
del _install_rng_recovery_semantics_v3

# Late semantic/UI wrappers are allowed to change presentation, but no catalog result
# may lose its implementation contract as a side effect.
from .final_contracts_v3 import install as _install_final_contracts_v3

_install_final_contracts_v3()
del _install_final_contracts_v3
