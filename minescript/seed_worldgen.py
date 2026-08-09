from __future__ import annotations

import hashlib
import json
import os
import queue
import re
import shutil
import subprocess
import threading
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

MANIFEST_URL = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
CACHE_ROOT = Path.home() / ".f3plus" / "minecraft-worldgen"
USER_AGENT = "F3Plus/2.0.0"


class WorldgenError(RuntimeError):
    pass


@dataclass(frozen=True)
class ServerArtifact:
    version_id: str
    url: str
    sha1: str
    path: Path
    java_major: int | None = None


def canonical_version_id(value: str) -> str:
    text = str(value or "").strip()
    m = re.fullmatch(r"(\d+\.\d+)\s+Snapshot\s+(\d+)", text, re.I)
    if m:
        return f"{m.group(1)}-snapshot-{m.group(2)}"
    return text.lower().replace(" ", "-")


def _json_url(url: str, timeout: int = 30) -> dict[str, Any]:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def resolve_server_artifact(version: str, *, cache_root: Path = CACHE_ROOT) -> ServerArtifact:
    version_id = canonical_version_id(version)
    manifest = _json_url(MANIFEST_URL)
    row = next((v for v in manifest.get("versions", []) if v.get("id") == version_id), None)
    if row is None:
        latest = manifest.get("latest", {})
        raise WorldgenError(
            f"Minecraft version {version!r} ({version_id}) is not present in Mojang's launcher manifest. "
            f"Latest release={latest.get('release')}, snapshot={latest.get('snapshot')}."
        )
    version_meta = _json_url(str(row["url"]))
    server = version_meta.get("downloads", {}).get("server")
    if not isinstance(server, dict) or not server.get("url") or not server.get("sha1"):
        raise WorldgenError(f"Mojang does not publish a server jar for {version_id}.")
    java_major = None
    java_meta = version_meta.get("javaVersion")
    if isinstance(java_meta, dict):
        try:
            java_major = int(java_meta.get("majorVersion"))
        except (TypeError, ValueError):
            java_major = None
    path = cache_root / "servers" / version_id / "server.jar"
    return ServerArtifact(version_id, str(server["url"]), str(server["sha1"]), path, java_major)


def _sha1(path: Path) -> str:
    h = hashlib.sha1()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def acquire_server(version: str, *, cache_root: Path = CACHE_ROOT) -> ServerArtifact:
    artifact = resolve_server_artifact(version, cache_root=cache_root)
    artifact.path.parent.mkdir(parents=True, exist_ok=True)
    if artifact.path.is_file() and _sha1(artifact.path) == artifact.sha1:
        return artifact
    tmp = artifact.path.with_suffix(".download")
    req = urllib.request.Request(artifact.url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=120) as response, tmp.open("wb") as out:
        shutil.copyfileobj(response, out)
    actual = _sha1(tmp)
    if actual != artifact.sha1:
        tmp.unlink(missing_ok=True)
        raise WorldgenError(f"Server jar SHA-1 mismatch for {artifact.version_id}: expected {artifact.sha1}, got {actual}.")
    os.replace(tmp, artifact.path)
    return artifact


def _java_major(executable: str | Path) -> int | None:
    try:
        proc = subprocess.run(
            [str(executable), "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=12,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    text = proc.stdout or ""
    match = re.search(r'(?:java|openjdk)\s+version\s+"?(\d+)', text, re.I)
    if not match:
        match = re.search(r'version\s+"?(\d+)', text, re.I)
    return int(match.group(1)) if match else None


def _minecraft_roots() -> list[Path]:
    roots: list[Path] = []
    appdata = os.environ.get("APPDATA")
    if appdata:
        roots.append(Path(appdata) / ".minecraft")
    home = Path.home()
    roots.extend([
        home / ".minecraft",
        home / "Library" / "Application Support" / "minecraft",
    ])
    out: list[Path] = []
    for root in roots:
        try:
            if root.exists() and root not in out:
                out.append(root)
        except OSError:
            pass
    return out


def _java_candidates(explicit: str | None = None) -> list[str]:
    values: list[str] = []

    def add(value: str | Path | None):
        if not value:
            return
        text = str(value)
        if text not in values:
            values.append(text)

    add(os.environ.get("F3PLUS_JAVA"))
    if explicit and explicit != "java":
        add(explicit)
    java_home = os.environ.get("JAVA_HOME")
    if java_home:
        add(Path(java_home) / "bin" / ("java.exe" if os.name == "nt" else "java"))
    add(shutil.which(explicit or "java"))
    add(shutil.which("java"))

    executable_name = "java.exe" if os.name == "nt" else "java"
    # The official launcher normally keeps the game runtimes under .minecraft/runtime.
    # Prefer these before asking the player to install another JDK.
    for root in _minecraft_roots():
        runtime = root / "runtime"
        if not runtime.is_dir():
            continue
        try:
            for candidate in runtime.rglob(executable_name):
                if candidate.parent.name == "bin":
                    add(candidate)
        except OSError:
            continue
    return values


def resolve_java_runtime(required_major: int | None, explicit: str | None = None) -> tuple[str, int | None]:
    checked: list[tuple[str, int | None]] = []
    for candidate in _java_candidates(explicit):
        major = _java_major(candidate)
        if major is None:
            continue
        checked.append((candidate, major))
        if required_major is None or major >= required_major:
            return candidate, major
    if required_major is None and explicit:
        return explicit, _java_major(explicit)
    found = ", ".join(f"Java {major} at {path}" for path, major in checked[:5]) or "no usable Java runtime"
    raise WorldgenError(
        f"This Minecraft version requires Java {required_major or 'a compatible runtime'}, but F3+ found {found}. "
        "Start the selected Minecraft version once through the official launcher so its bundled runtime is installed, "
        "or set F3PLUS_JAVA / JAVA_HOME to a compatible Java executable."
    )


def _chunk_rectangles(cx: int, cz: int, radius: int, tile: int = 16):
    min_cx, max_cx = cx - radius, cx + radius
    min_cz, max_cz = cz - radius, cz + radius
    for x0 in range(min_cx, max_cx + 1, tile):
        x1 = min(max_cx, x0 + tile - 1)
        for z0 in range(min_cz, max_cz + 1, tile):
            z1 = min(max_cz, z0 + tile - 1)
            yield x0, z0, x1, z1


def _write_properties(root: Path, seed: int, level_name: str):
    props = {
        "allow-flight": "true",
        "difficulty": "peaceful",
        "enable-command-block": "false",
        "enable-query": "false",
        "enable-rcon": "false",
        "enforce-secure-profile": "false",
        "force-gamemode": "false",
        "generate-structures": "true",
        "level-name": level_name,
        "level-seed": str(seed),
        "max-players": "1",
        "motd": "F3+ deterministic worldgen",
        "online-mode": "false",
        "pause-when-empty-seconds": "-1",
        "simulation-distance": "3",
        "spawn-protection": "0",
        "sync-chunk-writes": "true",
        "view-distance": "3",
    }
    (root / "server.properties").write_text("\n".join(f"{k}={v}" for k, v in props.items()) + "\n", encoding="utf-8")


def _reader(stream, out: queue.Queue[str]):
    try:
        for line in iter(stream.readline, ""):
            out.put(line.rstrip())
    finally:
        out.put("__F3PLUS_EOF__")


def _wait_for(lines: queue.Queue[str], predicate, timeout: float, log: list[str]) -> str:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            line = lines.get(timeout=0.25)
        except queue.Empty:
            continue
        log.append(line)
        if line == "__F3PLUS_EOF__":
            excerpt = "\n".join(log[-18:])
            raise WorldgenError("Minecraft's local reference server stopped before generation completed.\n" + excerpt)
        if predicate(line):
            return line
    raise WorldgenError("Timed out waiting for Minecraft's local reference server to generate the requested chunks.\n" + "\n".join(log[-18:]))


def _find_overworld_root(target: Path, preferred: Path) -> Path | None:
    candidates = [preferred, target]
    candidates.extend(path.parent for path in target.rglob("region") if path.is_dir())
    seen: set[Path] = set()
    for root in candidates:
        try:
            resolved = root.resolve()
        except OSError:
            resolved = root
        if resolved in seen:
            continue
        seen.add(resolved)
        region = root / "region"
        if region.is_dir() and any(region.glob("r.*.*.mca")):
            return root
    return None


def generate_reference_world(
    seed: int,
    version: str,
    *,
    center_chunk: tuple[int, int] = (0, 0),
    radius_chunks: int = 4,
    dimension: str = "Overworld",
    java: str | None = None,
    accept_eula: bool = False,
    cache_root: Path = CACHE_ROOT,
    max_chunks: int = 4096,
    startup_timeout: float = 180.0,
) -> Path:
    """Materialize exact vanilla chunks from seed using Mojang's matching server jar."""
    if not accept_eula:
        raise WorldgenError("Exact seed regeneration needs explicit Minecraft EULA acceptance for the temporary local server run.")
    dim = str(dimension).lower()
    if dim not in {"overworld", "0"}:
        raise WorldgenError("Exact seed regeneration currently supports Overworld chunks only.")
    radius = max(0, int(radius_chunks))
    requested = (2 * radius + 1) ** 2
    if requested > int(max_chunks):
        raise WorldgenError(f"The requested area is {requested:,} chunks, above the configured exact-generation limit of {max_chunks:,}. Reduce the radius or raise the limit knowingly.")
    cx, cz = map(int, center_chunk)
    artifact = acquire_server(version, cache_root=cache_root)
    java_executable, java_major = resolve_java_runtime(artifact.java_major, java)
    key = hashlib.sha256(f"{artifact.version_id}|{int(seed)}|{cx}|{cz}|{radius}".encode()).hexdigest()[:20]
    target = cache_root / "worlds" / artifact.version_id / str(int(seed)) / key
    preferred_world = target / "world"
    marker = target / ".f3plus-worldgen.json"
    if marker.is_file():
        try:
            meta = json.loads(marker.read_text(encoding="utf-8"))
            cached = target / str(meta.get("world_relative", "world"))
            found = _find_overworld_root(target, cached)
            if found is not None:
                return found
        except (OSError, ValueError, json.JSONDecodeError):
            pass
    target.mkdir(parents=True, exist_ok=True)
    _write_properties(target, int(seed), "world")
    (target / "eula.txt").write_text("eula=true\n", encoding="utf-8")

    proc = subprocess.Popen(
        [java_executable, "-Xms512M", "-Xmx2G", "-jar", str(artifact.path), "nogui"],
        cwd=target,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    if proc.stdin is None or proc.stdout is None:
        raise WorldgenError("Could not open the local Minecraft server command streams.")
    lines: queue.Queue[str] = queue.Queue()
    log: list[str] = []
    threading.Thread(target=_reader, args=(proc.stdout, lines), daemon=True).start()
    try:
        _wait_for(lines, lambda line: "Done (" in line or "Done (" in line.replace(",", "."), startup_timeout, log)
        for x0, z0, x1, z1 in _chunk_rectangles(cx, cz, radius):
            proc.stdin.write(f"forceload add {x0 * 16} {z0 * 16} {x1 * 16 + 15} {z1 * 16 + 15}\n")
        proc.stdin.write("save-all flush\n")
        proc.stdin.flush()
        _wait_for(lines, lambda line: "Saved the game" in line or "Saving the game" in line, max(30.0, requested * 0.15), log)
        time.sleep(min(30.0, max(2.0, requested * 0.03)))
        proc.stdin.write("save-all flush\n")
        proc.stdin.write("stop\n")
        proc.stdin.flush()
        proc.wait(timeout=120)
    except Exception:
        try:
            proc.stdin.write("stop\n")
            proc.stdin.flush()
        except Exception:
            pass
        try:
            proc.wait(timeout=10)
        except Exception:
            proc.kill()
        raise
    finally:
        try:
            proc.stdin.close()
        except Exception:
            pass
        try:
            proc.stdout.close()
        except Exception:
            pass
    if proc.returncode not in (0, None):
        raise WorldgenError(f"Minecraft's local reference server exited with code {proc.returncode}.\n" + "\n".join(log[-18:]))
    world = _find_overworld_root(target, preferred_world)
    if world is None:
        raise WorldgenError("Minecraft finished the local reference run, but F3+ could not find the generated Overworld region files.")
    try:
        rel = str(world.relative_to(target))
    except ValueError:
        rel = str(world)
    marker.write_text(json.dumps({
        "version": artifact.version_id,
        "seed": int(seed),
        "center_chunk": [cx, cz],
        "radius_chunks": radius,
        "server_sha1": artifact.sha1,
        "java_major_required": artifact.java_major,
        "java_major_used": java_major,
        "java_executable": java_executable,
        "source": "official Mojang server reference generation",
        "world_relative": rel,
    }, indent=2), encoding="utf-8")
    return world


def resolve_world_source(params: dict[str, Any], executor=None, *, default_radius: int = 8) -> tuple[str | None, dict[str, Any]]:
    """Resolve a generated-save or seed-regenerated world for terrain analyzers."""
    supplied = str(params.get("world_path", "")).strip()
    if supplied:
        return supplied, {"source": "generated-world save", "exactness": "observed generated chunks"}
    if not bool(params.get("regenerate_from_seed", True)):
        return None, {"requires_generated_world": True, "reason": "No world save selected and exact seed regeneration is disabled."}
    version = str(params.get("minecraft_version") or getattr(executor, "minecraft_version", "26.3 Snapshot 7"))
    seed = int(str(params.get("seed", 0)).strip())
    radius = max(0, int(params.get("radius", default_radius)))
    max_chunks = max(1, int(params.get("worldgen_max_chunks", 4096)))
    try:
        world = generate_reference_world(
            seed,
            version,
            center_chunk=(int(params.get("cx", 0)), int(params.get("cz", 0))),
            radius_chunks=radius,
            dimension=str(params.get("dimension", "Overworld")),
            java=str(params.get("java", "")).strip() or None,
            accept_eula=bool(params.get("accept_minecraft_eula", False)),
            max_chunks=max_chunks,
        )
    except (WorldgenError, OSError, ValueError) as exc:
        return None, {
            "requires_seed_worldgen": True,
            "available": False,
            "reason": str(exc),
            "version": version,
            "seed": seed,
            "requested_radius_chunks": radius,
            "next_step": "Select an existing generated save, or let F3+ use a compatible Minecraft Launcher Java runtime for exact seed regeneration.",
        }
    return str(world), {
        "source": "seed-regenerated vanilla chunks",
        "exactness": "official Mojang server reference generation",
        "version": canonical_version_id(version),
        "seed": seed,
        "world_path": str(world),
    }
