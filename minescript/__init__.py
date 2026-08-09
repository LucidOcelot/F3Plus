__version__ = "1.16.3"
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
