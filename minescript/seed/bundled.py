from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import ctypes, os, platform, shutil, subprocess
from ..runtime_deps import find_or_acquire_c_compiler, acquire_nether_bedrock_cracker

ROOT = Path(__file__).resolve().parents[2]
THIRD_PARTY = ROOT / 'third_party'
CUBIOMES = THIRD_PARTY / 'cubiomes'
BEDROCK = THIRD_PARTY / 'nether_bedrock_cracker'

@dataclass(frozen=True)
class BundledTool:
    name: str
    source_dir: Path
    available: bool
    executable: Path | None = None
    library: Path | None = None
    note: str = ''


def _cubiomes_library_candidates():
    names = ['cubiomes.dll'] if os.name == 'nt' else (['libcubiomes.dylib'] if platform.system() == 'Darwin' else ['libcubiomes.so'])
    for name in names:
        yield CUBIOMES / 'build' / name
        yield CUBIOMES / name


def cubiomes_status() -> BundledTool:
    if not (CUBIOMES / 'generator.c').exists():
        return BundledTool('cubiomes', CUBIOMES, False, note='Bundled Cubiomes source is not present.')
    lib = next((p for p in _cubiomes_library_candidates() if p.exists()), None)
    return BundledTool('cubiomes', CUBIOMES, True, library=lib,
                       note='Bundled source present; shared library will be built on demand.' if lib is None else 'Bundled source and shared library present.')


def build_cubiomes() -> Path:
    status = cubiomes_status()
    if not status.available:
        raise RuntimeError(status.note)
    if status.library:
        return status.library
    build = CUBIOMES / 'build'; build.mkdir(exist_ok=True)
    src = ['generator.c','layers.c','biomes.c','biomenoise.c','noise.c','finders.c','util.c','quadbase.c']
    compiler, compiler_name = find_or_acquire_c_compiler()
    if compiler_name == 'cl':
        out = build / 'cubiomes.dll'
        bridge = ROOT / 'minescript' / 'seed' / 'cubiomes_bridge.c'
        args = compiler + ['/O2','/LD','/I'+str(CUBIOMES), '/Fe:'+str(out)] + [str(CUBIOMES / x) for x in src] + [str(bridge)]
    else:
        out = build / ('cubiomes.dll' if os.name == 'nt' else ('libcubiomes.dylib' if platform.system() == 'Darwin' else 'libcubiomes.so'))
        bridge = ROOT / 'minescript' / 'seed' / 'cubiomes_bridge.c'
        args = compiler + ['-O3','-fPIC','-shared','-fwrapv','-I',str(CUBIOMES),'-o',str(out)] + [str(CUBIOMES / x) for x in src] + [str(bridge),'-lm']
    subprocess.run(args, check=True, cwd=CUBIOMES)
    if not out.exists():
        raise RuntimeError(f'Cubiomes compiler completed but did not create {out}')
    return out


def load_cubiomes():
    return ctypes.CDLL(str(build_cubiomes()))


def _bedrock_binary_names() -> list[str]:
    system = platform.system()
    if system == 'Windows':
        return ['cracker_gui-x86_64-pc-windows-msvc.exe', 'bedrock_cracker.exe', 'cracker_gui.exe']
    if system == 'Darwin':
        machine = platform.machine().lower()
        names = ['cracker_gui-x86_64-apple-darwin', 'bedrock_cracker', 'cracker_gui']
        # Upstream currently publishes x86_64 macOS; Rosetta may be required on arm64.
        return names
    return ['bedrock_cracker-x86_64-unknown-linux-gnu', 'bedrock_cracker', 'cracker_gui']


def bedrock_status() -> BundledTool:
    names = _bedrock_binary_names()
    roots = [BEDROCK / 'bin', BEDROCK, BEDROCK / 'target' / 'release']
    candidates = [root / name for root in roots for name in names]
    exe = next((p for p in candidates if p.exists() and p.is_file()), None)
    source_roots = [BEDROCK, BEDROCK / 'source']
    source = next((p for p in source_roots if (p / 'Cargo.toml').exists()), None)
    return BundledTool(
        'Nether Bedrock Cracker', source or BEDROCK, bool(exe or source), executable=exe,
        note='Bundled executable present.' if exe else (
            'Bundled Rust source present; build required.' if source else
            'Bundled Nether Bedrock Cracker is not present.'
        ),
    )
