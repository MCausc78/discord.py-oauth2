"""
Discord API Wrapper
~~~~~~~~~~~~~~~~~~~

A basic wrapper for the Discord API.

:copyright: (c) 2015-present Rapptz
:license: MIT, see LICENSE for more details.

"""

__title__ = 'discord'
__author__ = 'Rapptz'
__license__ = 'MIT'
__copyright__ = 'Copyright 2015-present Rapptz'
__version__ = '2.6.0a'

__path__ = __import__('pkgutil').extend_path(__path__, __name__)

import logging
from typing import NamedTuple, Literal

from . import (
    abc as abc,
    opus as opus,
    utils as utils,
)
from .activity import *
from .appinfo import *
from .asset import *
from .automod import *
from .channel import *
from .client import *
from .client_properties import *
from .colour import *
from .components import *
from .connections import *
from .embeds import *
from .emoji import *
from .enums import *
from .errors import *
from .file import *
from .flags import *
from .game_relationship import *
from .guild import *
from .integrations import *
from .invite import *
from .lobby import *
from .member import *
from .mentions import *
from .message import *
from .object import *
from .partial_emoji import *
from .permissions import *
from .player import *
from .poll import *
from .presences import *
from .raw_models import *
from .reaction import *
from .relationship import *
from .role import *
from .settings import *
from .scheduled_event import *
from .sku import *
from .soundboard import *
from .stage_instance import *
from .sticker import *
from .subscription import *
from .team import *
from .template import *
from .threads import *
from .user import *
from .voice_client import *
from .webhook import *
from .welcome_screen import *
from .widget import *


class VersionInfo(NamedTuple):
    major: int
    minor: int
    micro: int
    releaselevel: Literal["alpha", "beta", "candidate", "final"]
    serial: int


version_info: VersionInfo = VersionInfo(major=2, minor=6, micro=0, releaselevel='alpha', serial=0)

logging.getLogger(__name__).addHandler(logging.NullHandler())

del logging, NamedTuple, Literal, VersionInfo
