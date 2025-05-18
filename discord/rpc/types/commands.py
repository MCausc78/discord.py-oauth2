from __future__ import annotations

from typing import List, TypedDict
from typing_extensions import NotRequired

from ..types.oauth2 import GetCurrentAuthorizationInformationResponse
from ..types.snowflake import Snowflake


class SetConfigCommandRequest(TypedDict):
    use_interactive_pip: bool


class SetConfigCommandResponse(TypedDict):
    use_interactive_pip: bool


class AuthorizeCommandRequest(TypedDict):
    client_id: Snowflake
    response_type: NotRequired[str]
    scopes: NotRequired[List[str]]  # This takes priority over scope
    scope: NotRequired[List[str]]  # Deprecated I think?


class AuthorizeCommandResponse(TypedDict):
    code: str


class AuthenticateCommandResponse(GetCurrentAuthorizationInformationResponse):
    access_token: str
