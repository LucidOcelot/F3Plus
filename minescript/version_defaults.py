from __future__ import annotations


def install() -> None:
    """Keep direct/library FeatureExecutor construction on the current F3+ target."""
    from . import TARGET_MINECRAFT
    from .feature_executor import FeatureExecutor

    if getattr(FeatureExecutor, "_v2_default_version_installed", False):
        return
    original_init = FeatureExecutor.__init__

    def init(self, minecraft_version=TARGET_MINECRAFT):
        original_init(self, minecraft_version)

    FeatureExecutor.__init__ = init
    FeatureExecutor._v2_default_version_installed = True
