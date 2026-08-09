#!/bin/sh
set -u
cd "$(dirname "$0")" || exit 1
ROOT="$PWD"
LOG="$ROOT/F3Plus_startup.log"
RUNTIME="$ROOT/.runtime"
UV_DIR="$RUNTIME/uv"
UV="$UV_DIR/uv"
UV_VERSION='0.12.0'

echo 'F3+ 2.4.0 - LucidOcelot'
echo '=================================='
echo
echo 'Checking installation...'

for required in launcher.py main.py requirements.txt minescript/app.py updater.py; do
  if [ ! -e "$ROOT/$required" ]; then
    echo 'ERROR: F3+ is not fully extracted.'
    echo 'Extract the entire ZIP to a normal folder and try again.'
    exit 1
  fi
done

find_python() {
  for p in "$RUNTIME/python"/*/bin/python3 "$RUNTIME/python"/*/bin/python "$RUNTIME/python/bin/python3" "$RUNTIME/python/bin/python"; do
    [ -x "$p" ] || continue
    "$p" -c 'import sys; raise SystemExit(0 if (3,11) <= sys.version_info[:2] <= (3,13) else 1)' >/dev/null 2>&1 && { printf '%s\n' "$p"; return 0; }
  done
  for name in python3 python; do
    command -v "$name" >/dev/null 2>&1 || continue
    p=$(command -v "$name")
    "$p" -c 'import sys; raise SystemExit(0 if (3,11) <= sys.version_info[:2] <= (3,13) else 1)' >/dev/null 2>&1 && { printf '%s\n' "$p"; return 0; }
  done
  return 1
}

PYTHON=$(find_python || true)
if [ -z "$PYTHON" ]; then
  echo 'Python 3.11 through 3.13 was not found. F3+ will prepare a private runtime.'
  mkdir -p "$UV_DIR" "$RUNTIME/python" || exit 2
  if [ ! -x "$UV" ]; then
    command -v curl >/dev/null 2>&1 || { echo 'ERROR: curl is required for automatic first-run setup.'; exit 3; }
    ARCH=$(uname -m)
    case "$ARCH" in
      x86_64|amd64)
        UV_ASSET='uv-x86_64-unknown-linux-gnu.tar.gz'
        UV_SHA256='eaf842262aa1c418d8ecc5605f02ee1ebfd369124fa48548e85f9481a47831a9'
        ;;
      aarch64|arm64)
        UV_ASSET='uv-aarch64-unknown-linux-gnu.tar.gz'
        UV_SHA256='2c5d6e3092cc5223b10ff403880cc75121bf64e84644e7a0c69f643b0d89ac95'
        ;;
      *) echo "ERROR: Automatic runtime setup does not support Linux architecture $ARCH."; exit 3 ;;
    esac
    UV_ARCHIVE="$RUNTIME/$UV_ASSET"
    UV_URL="https://releases.astral.sh/github/uv/releases/download/$UV_VERSION/$UV_ASSET"
    echo "Downloading the verified project-local runtime bootstrap (uv $UV_VERSION)..."
    curl --proto '=https' --tlsv1.2 -fL "$UV_URL" -o "$UV_ARCHIVE" || { echo 'ERROR: Could not download the runtime bootstrap.'; exit 4; }
    if command -v sha256sum >/dev/null 2>&1; then
      ACTUAL=$(sha256sum "$UV_ARCHIVE" | awk '{print $1}')
    elif command -v shasum >/dev/null 2>&1; then
      ACTUAL=$(shasum -a 256 "$UV_ARCHIVE" | awk '{print $1}')
    else
      rm -f "$UV_ARCHIVE"; echo 'ERROR: SHA-256 utility is required to verify the runtime bootstrap.'; exit 4
    fi
    [ "$ACTUAL" = "$UV_SHA256" ] || { rm -f "$UV_ARCHIVE"; echo 'ERROR: Runtime bootstrap failed SHA-256 verification.'; exit 4; }
    echo 'Runtime bootstrap download verified.'
    tar -xzf "$UV_ARCHIVE" -C "$UV_DIR" || { rm -f "$UV_ARCHIVE"; echo 'ERROR: Could not unpack the verified runtime bootstrap.'; exit 4; }
    rm -f "$UV_ARCHIVE"
    FOUND_UV=$(find "$UV_DIR" -type f -name uv -perm -u+x 2>/dev/null | head -n 1)
    [ -n "$FOUND_UV" ] || { echo 'ERROR: Verified uv archive did not contain uv.'; exit 4; }
    cp "$FOUND_UV" "$UV" && chmod +x "$UV" || { echo 'ERROR: Could not prepare uv.'; exit 4; }
  fi
  export UV_PYTHON_INSTALL_DIR="$RUNTIME/python" UV_NO_MODIFY_PATH=1
  echo 'Downloading a private Python 3.13 runtime...'
  "$UV" python install 3.13 || { echo 'ERROR: Could not prepare Python.'; exit 5; }
  PYTHON=$(find_python || true)
  if [ -z "$PYTHON" ]; then
    PYTHON=$(UV_PYTHON_PREFERENCE=only-managed "$UV" python find 3.13 2>/dev/null || true)
  fi
  [ -n "$PYTHON" ] && [ -x "$PYTHON" ] || { echo 'ERROR: Private Python was installed but could not be located.'; exit 6; }
fi

PYVER=$($PYTHON -c 'import sys; print(sys.version.split()[0])' 2>/dev/null || echo unknown)
echo "Found Python $PYVER"
echo 'Starting F3+ setup and launch...'
echo 'F3+ checks GitHub for updates before loading the application; offline launch continues if the check cannot connect.'
"$PYTHON" "$ROOT/launcher.py"
RC=$?
if [ "$RC" -ne 0 ]; then
  echo "F3+ could not finish starting (exit code $RC)."
  echo "Startup log: $LOG"
fi
exit "$RC"