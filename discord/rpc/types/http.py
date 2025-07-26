from __future__ import annotations

from typing import Any, Dict, Optional, TypedDict


class Response(TypedDict):
    ok: bool
    headers: Dict[str, str]
    body: Optional[Any]
    status: int
