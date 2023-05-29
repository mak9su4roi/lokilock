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
    ) as repository, httpx.AsyncClient(
        base_url=os.environ["VERIFICATION_URL"]
    ) as verification:
        resources["verification"] = verification
        resources["repository"] = repository
        resources["model"] = servernet_face.load()
        yield
    resources.clear()


app = FastAPI(lifespan=lifespan)


async def invalidate(lock_id):
    res = await resources["verification"].delete(f"/cash/{lock_id}/")
    logger.info(f"{res=}")
    return res.json()


@app.post("/{lock_id}/", status_code=status.HTTP_201_CREATED)
async def add_users(lock_id: LockId, req: enrollment.LockUsers):
    await resources["repository"].post(
        f"/{lock_id}/",
        data=repository.LockUsers(
            users={
                user: [Vector(data=resources["model"](v)) for v in data]
                for user, data in req.users.items()
            },
        ).json(),
    )
    await invalidate(lock_id)


@app.delete("/{lock_id}/")
async def remove_lock(
    lock_id: str,
):
    res = (await resources["repository"].delete(f"/{lock_id}/")).json()
    await invalidate(lock_id)
    return res


@app.delete("/{lock_id}/{user_id}")
async def remove_user(lock_id: str, user_id: str):
    res = (await resources["repository"].delete(f"/{lock_id}/{user_id}")).json()
    await invalidate(lock_id)
    return res
