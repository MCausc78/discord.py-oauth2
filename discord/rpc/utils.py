"""
The MIT License (MIT)

Copyright (c) 2025-present MCausc78

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""

from __future__ import annotations

import base64
import hashlib
from inspect import isawaitable
import os
from os.path import abspath, exists, isdir, join
import socket
from sys import platform
from tempfile import gettempdir
from typing import Awaitable, Callable, List, Optional, TYPE_CHECKING, Tuple, TypeVar, Union

from ..enums import OAuth2CodeChallengeMethod, OAuth2ResponseType
from ..utils import MISSING

if TYPE_CHECKING:
    from ..abc import Snowflake
    from ..client import Client as NormalClient
    from ..enums import ExternalAuthenticationProviderType, InstallationType
    from ..oauth2 import AccessToken
    from ..permissions import Permissions
    from .client import Client
    from .enums import PromptBehavior

    C = TypeVar('C', bound='Client')
    NC = TypeVar('NC', bound='NormalClient')

__all__ = (
    'get_ipc_path',
    'test_ipc_path',
    'quick_authorize',
)

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


def default_upgrader(client: Client) -> NormalClient:
    from ..client import Client as NormalClient

    return NormalClient(rpc=client)


async def quick_authorize(
    client: C,
    id: int,
    *,
    upgrader: Callable[[C], Union[NC, Awaitable[NC]]] = default_upgrader,
    scopes: Optional[List[str]] = None,
    state: Optional[str] = None,
    nonce: Optional[str] = None,
    permissions: Optional[Permissions] = None,
    guild: Optional[Snowflake] = None,
    channel: Optional[Snowflake] = None,
    prompt: Optional[PromptBehavior] = None,
    disable_guild_select: Optional[bool] = None,
    install_type: Optional[InstallationType] = None,
    pid: Optional[int] = MISSING,
    external_auth_token: Optional[str] = None,
    external_auth_type: Optional[ExternalAuthenticationProviderType] = None,
) -> Tuple[AccessToken, NC]:
    code_verifier = base64.urlsafe_b64encode(os.urandom(32)).rstrip(b'=').decode('utf-8')
    code_challenge = (
        base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode('utf-8')).digest()).decode('utf-8').rstrip('=')
    )
    code = await client.authorize(
        id,
        response_type=OAuth2ResponseType.code,
        scopes=scopes,
        code_challenge=code_challenge,
        code_challenge_method=OAuth2CodeChallengeMethod.sha256,
        state=state,
        nonce=nonce,
        permissions=permissions,
        guild=guild,
        channel=channel,
        prompt=prompt,
        disable_guild_select=disable_guild_select,
        install_type=install_type,
        pid=pid,
    )

    tmp = upgrader(client)
    if isawaitable(tmp):
        upgraded = await tmp
    else:
        upgraded = tmp

    result = await upgraded.exchange_code(
        id,
        code=code,
        code_verifier=code_verifier,
        external_auth_token=external_auth_token,
        external_auth_type=external_auth_type,
    )
    await client.authenticate(result.access_token)
    await upgraded.login(result.access_token, validate=False)
    return (result, upgraded)
