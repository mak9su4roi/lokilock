from enum import IntEnum, auto
from typing import Union

from common.types.vector import Model, Vector

from .types import UserId


class AuthError(IntEnum):
    UNKNOWN_USER = auto()
    UNKNOWN_LOCK = auto()
    EMPTY_USERBASE = auto()


class AuthReq(Model):
    data: Vector


class AuthRsp(Model):
    status: Union[UserId, AuthError]
