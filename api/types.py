from typing import Optional, TypeVar

from common.types.vector import Model, Vector

LockId = TypeVar("LockId", bound=str)
UserId = TypeVar("UserId", bound=str)

Users = dict[UserId, tuple[Vector, ...]]


class LockUsers(Model):
    users: Optional[Users] = None
