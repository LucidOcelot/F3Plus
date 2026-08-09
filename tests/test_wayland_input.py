from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

from minescript.platform_input.linux import ydotool_socket_candidates


def test_ydotool_socket_candidates_prefers_explicit(tmp_path):
    explicit = tmp_path / "custom.sock"
    runtime = tmp_path / "runtime"
    with patch.dict(os.environ, {"YDOTOOL_SOCKET": str(explicit), "XDG_RUNTIME_DIR": str(runtime)}, clear=False):
        candidates = ydotool_socket_candidates()
    assert candidates[0] == explicit
    assert runtime / ".ydotool_socket" in candidates


def test_ydotool_socket_candidates_include_common_system_paths(tmp_path):
    with patch.dict(os.environ, {"XDG_RUNTIME_DIR": str(tmp_path)}, clear=False):
        candidates = ydotool_socket_candidates()
    assert Path("/tmp/.ydotool_socket") in candidates
    assert Path("/run/ydotoold/socket") in candidates
