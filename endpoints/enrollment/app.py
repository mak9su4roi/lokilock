import os
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, status

from api import enrollment, repository
from api.types import LockId
from common.logging.logger import logger
from common.types.vector import Vector
from models import servernet_face

resources = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with httpx.AsyncClient(
        base_url=os.environ["REPOSITORY_URL"]
    ) as repository:
        resources["repository"] = repository
        resources["model"] = servernet_face.load()
        logger.info("service is running")
        yield
    logger.info("service is down")
    resources.clear()


app = FastAPI(lifespan=lifespan)


@app.post("/{lock_id}/", status_code=status.HTTP_201_CREATED)
async def add_users(lock_id: LockId, req: enrollment.LockUsers):
    logger.info(f"registering users to {lock_id=}")
    await resources["repository"].post(
        f"/{lock_id}/",
        data=repository.LockUsers(
            users={
                user: [Vector(data=resources["model"](v)) for v in data]
                for user, data in req.users.items()
            },
        ).json(),
    )


@app.delete("/{lock_id}/")
async def remove_lock(
    lock_id: str,
):
    logger.info(f"unregistering {lock_id=}")
    res = (await resources["repository"].delete(f"/{lock_id}/")).json()
    return res


@app.delete("/{lock_id}/{user_id}")
async def remove_user(lock_id: str, user_id: str):
    logger.info(f"unregistering user from {lock_id=}")
    res = (await resources["repository"].delete(f"/{lock_id}/{user_id}")).json()
    return res
