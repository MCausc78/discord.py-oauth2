from __future__ import annotations

import os
from os.path import abspath, exists, isdir, join
import socket
from sys import platform
from tempfile import gettempdir
from typing import Optional

# Thank you qwertyqwerty
def get_ipc_path(pipe: Optional[int] = None) -> Optional[str]:
    """Returns on first IPC pipe matching Discord's."""
    ipc = 'discord-ipc-'
    if pipe is not None:
        ipc = ipc + str(pipe)

    if platform in ('linux', 'darwin'):
        tempdir = os.environ.get('XDG_RUNTIME_DIR')
        if tempdir is None:
            path = f"/run/user/{os.getuid()}"  # type: ignore
            if exists(path):
                tempdir = path
            else:
                tempdir = gettempdir()
        paths = [
            '.',
            '..',
            'snap.discord',
            'app/com.discordapp.Discord',
            'app/com.discordapp.DiscordCanary',
        ]
    elif platform == 'win32':
        tempdir = r'\\?\pipe'
        paths = ['.']
    else:
        return None

    for path in paths:
        full_path = abspath(join(tempdir, path))
        if platform != 'win32' and not isdir(full_path):
            continue
        for entry in os.scandir(full_path):
            if entry.name.startswith(ipc) and exists(entry) and test_ipc_path(entry.path):
                return entry.path


def test_ipc_path(path: str, /) -> bool:
    """Tests an IPC pipe to ensure that it actually works."""
    if platform == 'win32':
        with open(path, 'rb'):
            return True
    else:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:  # type: ignore
            s.connect(path)
            return True
