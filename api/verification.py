from enum import Enum, auto
from typing import Union

from common.types.vector import Model, Vector

from .types import UserId


class AuthError(Enum):
    UNKNOWN_USER = "Unknown user"
    UNKNOWN_LOCK = "Unregistered lock"
    CONNECTION = "Connection error"


class AuthReq(Model):
    data: Vector


class AuthRsp(Model):
    status: Union[AuthError, UserId]
