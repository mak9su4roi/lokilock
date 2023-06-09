import asyncio
from contextlib import asynccontextmanager
from enum import Enum, auto
from itertools import groupby
from typing import TYPE_CHECKING

import httpx
import redis.commands.search.aggregation as aggregations
import redis.commands.search.reducers as reducers
from fastapi import FastAPI
from pydantic import AnyUrl, BaseSettings
from redis.asyncio import ConnectionError, Redis
from redis.commands.search.query import Query

from api import repository, verification
from api.types import LockId
from common.logging.logger import logger
from models import servernet_face


class Settings(BaseSettings):
    index_port: int
    index_host: str
    repository_url: AnyUrl


if TYPE_CHECKING:
    import numpy as np
    import torch


class Index:
    class Fields(Enum):
        VECTOR = "vector"
        LOCK = "lock"
        USER = "user"

    class Status(Enum):
        EMPTY = auto()

    def __init__(self, host, port):
        self.__rs = Redis(host=host, port=port)

    @asynccontextmanager
    async def connect(self):
        while True:
            try:
                await self.__rs.ping()
            except ConnectionError:
                logger.info("Connecting to Index...")
                await asyncio.sleep(1)
            else:
                logger.info("Connected to Index")
                await asyncio.sleep(1)
                break
        try:
            await self.__rs.ft().config_set("default_dialect", 2)
            yield self
        finally:
            await self.__rs.close()

    async def _get_all_user_fv(self, lock_id: str):
        res = await self.__rs.ft().aggregate(
            aggregations.AggregateRequest(f"@lock:{lock_id}").group_by(
                "@user", reducers.count().alias("count")
            )
        )
        return {row[1].decode("utf-8"): int(row[3]) for row in res.rows}

    async def _get_similar_user_fv(
        self, lock_id: str, fv: "np.ndarray", th: float = 0.6
    ):
        res = await self.__rs.ft().search(
            Query(
                f"@{self.Fields.LOCK.value}:{lock_id}  "
                f"@{self.Fields.VECTOR.value}:[VECTOR_RANGE {th} $feature_vector]"
                f"=>{{$yield_distance_as: range_dist}}"
            )
            .paging(offset=0, num=1000)
            .return_field(self.Fields.USER.value),
            query_params=dict(feature_vector=fv.tobytes()),
        )
        return {
            name: len([*group])
            for name, group in groupby(
                [doc[self.Fields.USER.value] for doc in res.docs]
            )
        }

    async def append(
        self, vector: "np.ndarray", lock: str, user: str, vid: str, ttl: int = 60
    ):
        vid = f"{lock}-{user}-{vid}"
        await self.__rs.hset(
            vid,
            mapping={
                self.Fields.VECTOR.value: vector.tobytes(),
                self.Fields.USER.value: user,
                self.Fields.LOCK.value: lock,
            },
        )
        await self.__rs.expire(vid, ttl)

    async def recognize(
        self, lock_id, vector, th: float = 0.75
    ) -> "str | None | Index.Status":
        if not (u_all := await self._get_all_user_fv(lock_id)):
            return self.Status.EMPTY
        if not (u_sim := await self._get_similar_user_fv(lock_id, vector)):
            return None
        user, confidence = max(
            [(u, n / u_all[u]) for u, n in u_sim.items()], key=lambda i: i[1]
        )
        logger.info(f"{user=} {confidence=}")
        return user if confidence > th else None


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = Settings()
    async with (
        httpx.AsyncClient(base_url=settings.repository_url) as repository,
        Index(host=settings.index_host, port=settings.index_port).connect() as index,
    ):
        resources["repository"] = repository
        resources["model"] = servernet_face.load()
        resources["index"] = index
        yield
    resources.clear()


resources = {}
app = FastAPI(lifespan=lifespan)


async def recognize(lock_id: LockId, edge_vector: "torch.Tensor"):
    fv = resources["model"](edge_vector)
    index: Index = resources["index"]
    res = await index.recognize(lock_id, fv)
    if res is Index.Status.EMPTY:
        users = repository.LockUsers(
            **(await resources["repository"].get(f"/{lock_id}/")).json()
        ).users
        if users is not None:
            [
                await index.append(fv.data, lock_id, user, ind)
                for user, fvs in users.items()
                for ind, fv in enumerate(fvs)
            ]
            res = await index.recognize(lock_id, fv)
    return res


@app.post("/auth/{lock_id}/")
async def verify(lock_id: LockId, req: verification.AuthReq) -> verification.AuthRsp:
    logger.info(f"verifying user for {lock_id=}")
    match await recognize(lock_id, req.data.tensor):
        case Index.Status.EMPTY:
            logger.info(f"No {lock_id=} registred")
            return verification.AuthRsp(
                id=lock_id, status=verification.AuthError.UNKNOWN_LOCK
            )
        case None:
            logger.info(f"Unknown user")
            return verification.AuthRsp(
                id=lock_id, status=verification.AuthError.UNKNOWN_USER
            )
        case str(user):
            return verification.AuthRsp(id=lock_id, status=user)
