from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from minescript.platform_input.linux import LinuxYdotoolInput


def test_ydotool_backend_can_start_before_daemon_socket_exists():
    with patch("minescript.platform_input.linux.shutil.which", return_value="/usr/bin/ydotool"), patch(
        "minescript.platform_input.linux.find_ydotool_socket", return_value=None
    ):
        backend = LinuxYdotoolInput()
    assert backend.socket_path is None
    assert backend.capabilities.all_input_requires_focus


def test_ydotool_backend_rediscovers_socket_on_command(tmp_path):
    socket_path = tmp_path / ".ydotool_socket"
    backend = object.__new__(LinuxYdotoolInput)
    backend.exe = "/usr/bin/ydotool"
    backend.socket_path = None
    with patch("minescript.platform_input.linux.find_ydotool_socket", return_value=socket_path), patch(
        "minescript.platform_input.linux._is_socket", return_value=True
    ), patch("minescript.platform_input.linux.subprocess.run") as run:
        run.return_value.returncode = 0
        run.return_value.stderr = ""
        run.return_value.stdout = ""
        backend._invoke("key", "0:0")
    assert backend.socket_path == socket_path
    assert run.call_args.kwargs["env"]["YDOTOOL_SOCKET"] == str(socket_path)
