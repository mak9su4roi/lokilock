import pathlib
import shutil
import uuid

from fastapi import FastAPI, HTTPException, status

from api.repository import LockUsers
from api.types import LockId, UserId
from common.types.vector import Vector
from common.utils import async_timeit

resources = {}


async def lifespan(app: FastAPI):
    assert (s3 := pathlib.Path("/s3")).exists()
    resources["s3"] = s3
    yield
    resources.clear()


app = FastAPI(lifespan=lifespan)


@async_timeit
async def retriev(lock_id: str):
    return LockUsers(
        id=lock_id,
        users={
            d.name: [*map(Vector.from_file, d.iterdir())]
            for d in lock.iterdir()
            if d.is_dir()
        }
        if (lock := resources["s3"] / lock_id).exists()
        else None,
    )


@app.get("/{lock_id}/")
async def retrieve_lock_data(lock_id: str):
    res, time = await retriev(lock_id)
    print(f"Retrieval {time=}")
    return res


@app.post("/{lock_id}/", status_code=status.HTTP_201_CREATED)
async def store_lock_data(lock_id: LockId, req: LockUsers):
    (lock_folder := resources["s3"] / lock_id).exists() or lock_folder.mkdir()
    for user, data in req.users.items():
        (user_folder := lock_folder / user).exists() or user_folder.mkdir()
        [v.to_file(user_folder / f"{uuid.uuid4()}.npy") for v in data]


@app.delete("/{lock_id}/{user_id}")
async def delete_user_data(lock_id: LockId, user_id: UserId):
    s3 = resources["s3"]
    user_folder = s3 / lock_id / user_id
    if not user_folder.exists():
        raise HTTPException(status_code=404, detail="User not found")
    shutil.rmtree(user_folder)
    return {"OK": True}


@app.delete("/{lock_id}/")
async def delete_lock_data(lock_id: LockId):
    s3 = resources["s3"]
    lock_folder = s3 / lock_id
    if not lock_folder.exists():
        raise HTTPException(status_code=404, detail="Lock not found")
    shutil.rmtree(lock_folder)
    return {"OK": True}
