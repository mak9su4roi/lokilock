import argparse
import pathlib

import cv2
import httpx
from pydantic import validate_arguments

from api.enrollment import LockUsers
from common.logging.logger import logger
from common.types.vector import Vector
from models import blazeface, edgenet_face


@validate_arguments
def enroll_users(
    src: pathlib.Path,
):
    import torch

    assert src.exists()
    detector = blazeface.load()
    model = edgenet_face.load(device=torch.device("cpu"))
    users = {}
    for user in filter(lambda u: u.is_dir(), src.iterdir()):
        if user.name not in users:
            users[user.name] = []
        for file in user.iterdir():
            try:
                img = cv2.imread(file.as_posix())
                bbox, _ = max(detector(img), key=lambda r: r[1][0])
                face = blazeface.crop(img, bbox)
            except ValueError as err:
                print(f"Error: {file=} {err=}")
            else:
                users[user.name] += [Vector.from_tensor(model(face))]
    res = enrollment.post(f"/", data=LockUsers(users=users).json())
    logger.info(f"Enrollment status: {res}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("url", type=str)
    parser.add_argument("lock_id", type=str)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--enroll", type=pathlib.Path)
    group.add_argument("--delete", nargs="*")
    args = parser.parse_args()
    lock_id = args.lock_id
    with httpx.Client(base_url=f"{args.url}/{lock_id}") as enrollment:
        if (users := args.delete) is not None:
            if not users:
                res = enrollment.delete(f"/")
                logger.info(f"Deleteting {lock_id}: {res}")
            for user in users:
                res = enrollment.delete(f"/{user}")
                logger.info(f"Deleteting {user} form {lock_id}: {res}")
        if dataset := args.enroll:
            enroll_users(dataset)
