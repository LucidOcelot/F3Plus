from __future__ import annotations
from dataclasses import dataclass

TARGET_VERSION='26.3-snapshot-5'

@dataclass(frozen=True)
class FeatureSupport:
    feature:str
    selected_version:str
    implementation_version:str
    source:str
    confidence:str
    exact:bool
    note:str=''

# The table only records implementations shipped in F3+ itself. Optional community
# backends are resolved at runtime and report their own source/version instead of being mislabeled.
NATIVE={
    'coordinates':TARGET_VERSION,
    'slime_chunks':TARGET_VERSION,
    'portal_math':TARGET_VERSION,
    'build_calculators':TARGET_VERSION,
    'macro_engine':TARGET_VERSION,
}

def resolve_native(feature:str,selected_version:str=TARGET_VERSION):
    v=NATIVE.get(feature)
    if v:
        return FeatureSupport(feature,selected_version,v,'F3+','Native',True)
    return None
