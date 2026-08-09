__version__ = "2.0.0"
TARGET_MINECRAFT = "26.3 Snapshot 7"
STABLE_MINECRAFT = "26.2"

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

# Keep direct/library executor construction aligned with the current F3+ target.
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
