"""F3+ public package surface.

Importing :mod:`minescript` is intentionally side-effect free.  Engines, UI components,
and compatibility aliases are ordinary modules now; no class or function is rewritten
at package import time.
"""

from .version import VERSION as __version__, TARGET_MINECRAFT, STABLE_MINECRAFT

__all__ = ["__version__", "TARGET_MINECRAFT", "STABLE_MINECRAFT"]
