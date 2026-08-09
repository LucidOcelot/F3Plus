#!/bin/zsh
cd "$(dirname "$0")" || exit 1
ROOT="$PWD"
LOG="$ROOT/F3Plus_startup.log"
RUNTIME="$ROOT/.runtime"
UV_DIR="$RUNTIME/uv"
UV="$UV_DIR/uv"
UV_VERSION='0.12.0'
exec > >(tee -a "$LOG") 2>&1

printf 'F3+ 2.4.0 - LucidOcelot\n==================================\n\n'
echo 'Checking installation...'
for required in launcher.py main.py requirements.txt minescript/app.py updater.py; do
  if [ ! -e "$ROOT/$required" ]; then
    echo 'ERROR: F3+ is not fully extracted.'
    echo 'Extract the entire ZIP to a normal folder, then run START_F3PLUS.command again.'
    read '?Press Return to close...'
    exit 1
  fi
done

find_python() {
  local p
  for p in "$RUNTIME/python"/*/bin/python3 "$RUNTIME/python"/*/bin/python "$RUNTIME/python/bin/python3" "$RUNTIME/python/bin/python"; do
    [ -x "$p" ] || continue
    "$p" -c 'import sys; raise SystemExit(0 if (3,11) <= sys.version_info[:2] <= (3,13) else 1)' >/dev/null 2>&1 && { print -r -- "$p"; return 0; }
  done
  for p in /opt/homebrew/bin/python3 /usr/local/bin/python3 /Library/Frameworks/Python.framework/Versions/Current/bin/python3; do
    [ -x "$p" ] || continue
    "$p" -c 'import sys; raise SystemExit(0 if (3,11) <= sys.version_info[:2] <= (3,13) else 1)' >/dev/null 2>&1 && { print -r -- "$p"; return 0; }
  done
  for name in python3 python; do
    command -v "$name" >/dev/null 2>&1 || continue
    p="$(command -v "$name")"
    "$p" -c 'import sys; raise SystemExit(0 if (3,11) <= sys.version_info[:2] <= (3,13) else 1)' >/dev/null 2>&1 && { print -r -- "$p"; return 0; }
  done
  return 1
}

PYTHON="$(find_python 2>/dev/null || true)"
if [ -z "$PYTHON" ]; then
  echo 'Python 3.11 through 3.13 was not found. F3+ will prepare a private runtime.'
  mkdir -p "$UV_DIR" "$RUNTIME/python" || { echo 'ERROR: Could not create .runtime.'; read '?Press Return to close...'; exit 2; }
  if [ ! -x "$UV" ]; then
    if ! command -v curl >/dev/null 2>&1; then
      echo 'ERROR: curl is unavailable, so automatic setup cannot continue.'
      read '?Press Return to close...'; exit 3
    fi
    ARCH="$(uname -m)"
    case "$ARCH" in
      arm64|aarch64)
        UV_ASSET='uv-aarch64-apple-darwin.tar.gz'
        UV_SHA256='2b9e582af54f84fa50c115427451a6c13e80f43b52f8282b8af5791077317bbf'
        ;;
      x86_64)
        UV_ASSET='uv-x86_64-apple-darwin.tar.gz'
        UV_SHA256='d41593beaefc54bab7d062af0ef6ca093bfb81d001d58ebbef39e44423f9c496'
        ;;
      *) echo "ERROR: Automatic runtime setup does not support macOS architecture $ARCH."; read '?Press Return to close...'; exit 3 ;;
    esac
    UV_ARCHIVE="$RUNTIME/$UV_ASSET"
    UV_URL="https://releases.astral.sh/github/uv/releases/download/$UV_VERSION/$UV_ASSET"
    echo "Downloading the verified project-local runtime bootstrap (uv $UV_VERSION)..."
    if ! curl --proto '=https' --tlsv1.2 -fL "$UV_URL" -o "$UV_ARCHIVE"; then
      echo 'ERROR: Could not download the runtime bootstrap.'; read '?Press Return to close...'; exit 4
    fi
    ACTUAL="$(shasum -a 256 "$UV_ARCHIVE" | awk '{print $1}')"
    if [ "$ACTUAL" != "$UV_SHA256" ]; then
      rm -f "$UV_ARCHIVE"
      echo 'ERROR: Runtime bootstrap failed SHA-256 verification.'
      read '?Press Return to close...'; exit 4
    fi
    echo 'Runtime bootstrap download verified.'
    if ! tar -xzf "$UV_ARCHIVE" -C "$UV_DIR"; then
      rm -f "$UV_ARCHIVE"; echo 'ERROR: Could not unpack the verified runtime bootstrap.'; read '?Press Return to close...'; exit 4
    fi
    rm -f "$UV_ARCHIVE"
    FOUND_UV="$(find "$UV_DIR" -type f -name uv -perm -u+x 2>/dev/null | head -n 1)"
    if [ -z "$FOUND_UV" ]; then echo 'ERROR: Verified uv archive did not contain uv.'; read '?Press Return to close...'; exit 4; fi
    cp "$FOUND_UV" "$UV" && chmod +x "$UV" || { echo 'ERROR: Could not prepare uv.'; read '?Press Return to close...'; exit 4; }
  fi
  export UV_PYTHON_INSTALL_DIR="$RUNTIME/python" UV_NO_MODIFY_PATH=1
  echo 'Downloading a private Python 3.13 runtime...'
  if ! "$UV" python install 3.13; then
    echo 'ERROR: Could not prepare Python.'
    read '?Press Return to close...'; exit 5
  fi
  PYTHON="$(find_python 2>/dev/null || true)"
  if [ -z "$PYTHON" ]; then
    PYTHON="$(UV_PYTHON_PREFERENCE=only-managed "$UV" python find 3.13 2>/dev/null || true)"
  fi
  if [ -z "$PYTHON" ] || [ ! -x "$PYTHON" ]; then
    echo 'ERROR: Private Python was installed but could not be located.'
    read '?Press Return to close...'; exit 6
  fi
fi

PYVER="$($PYTHON -c 'import sys; print(sys.version.split()[0])')"
echo "Found Python $PYVER"
echo 'Starting F3+ setup and launch...'
echo 'F3+ checks GitHub for updates before loading the application; offline launch continues if the check cannot connect.'
"$PYTHON" "$ROOT/launcher.py"
RC=$?
if [ "$RC" -ne 0 ]; then
  echo
  echo "F3+ could not finish starting (exit code $RC)."
  echo "Startup log: $LOG"
  read '?Press Return to close...'
fi
exit "$RC"