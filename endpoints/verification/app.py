import os
import threading
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

import httpx
from fastapi import FastAPI

from api import repository, verification
from api.types import LockId
from common.logging.logger import logger
from models import servernet_face

if TYPE_CHECKING:
    import numpy as np
    import torch


class Cash:
    def __init__(self):
        self.__data = {}
        self.__lock = threading.Lock()

    def __getitem__(self, k):
        with self.__lock:
            return self.__data[k]

    def __setitem__(self, k, v):
        with self.__lock:
            self.__data[k] = v

    def __delitem__(self, k):
        with self.__lock:
            del self.__data[k]

    def __contains__(self, k):
        with self.__lock:
            return k in self.__data


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with httpx.AsyncClient(base_url=os.environ["REPOSITORY_URL"]) as client:
        resources["repository"] = client
        resources["model"] = servernet_face.load()
        resources["cash"] = Cash()
        yield
    resources.clear()


resources = {}
app = FastAPI(lifespan=lifespan)


async def to_feature_vector(edge_vector: "torch.Tensor") -> "np.ndarray":
    return resources["model"](edge_vector)


async def get_enrolled_users(lock_id: LockId):
    lock_cash = resources["cash"]
    if lock_id not in lock_cash:
        lock_cash[lock_id] = repository.LockUsers(
            **(await resources["repository"].get(f"/{lock_id}/")).json()
        ).users
    return lock_cash[lock_id]


@app.delete("/cash/{lock_id}/")
async def clear_lock_cash(lock_id: LockId):
    logger.info(f"Clearing cash for {lock_id=}")
    try:
        del resources["cash"][lock_id]
    except Exception as error:
        logger.error(str(error))


@app.post("/auth/{lock_id}/")
async def verify(lock_id: LockId, req: verification.AuthReq) -> verification.AuthRsp:
    match await get_enrolled_users(lock_id):
        case None:
            logger.info(f"No {lock_id=} registred")
            return verification.AuthRsp(
                id=lock_id, status=verification.AuthError.UNKNOWN_LOCK
            )
        case {} as users if not users:
            logger.info(f"No users for {lock_id=} registred")
            return verification.AuthRsp(
                id=lock_id, status=verification.AuthError.EMPTY_USERBASE
            )
    confidence, user = servernet_face.recognize(
        await to_feature_vector(req.data.tensor), users
    )
    logger.info(f"Recognized {user=} with {confidence=}")
    if confidence < 0.7:
        return verification.AuthRsp(
            id=lock_id, status=verification.AuthError.UNKNOWN_USER
        )
    return verification.AuthRsp(id=lock_id, status=user)
