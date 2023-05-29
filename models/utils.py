import pathlib
from typing import Union

import cv2
import numpy as np
import torch

REQUIRED_SHAPE = (128, 128)


def load_image(image: Union[pathlib.Path, np.ndarray]):
    if isinstance(image, pathlib.Path):
        assert (image := cv2.imread(image.as_posix(), 0)) is not None
    elif isinstance(image, np.ndarray):
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        raise RuntimeError(f"Unexpected type: {type(image)=}")
    image.shape == REQUIRED_SHAPE or (
        image := cv2.resize(image, REQUIRED_SHAPE, interpolation=cv2.INTER_AREA)
    )
    image = np.dstack((image, np.fliplr(image)))
    image = image.transpose((2, 0, 1))
    image = image[:, np.newaxis, :, :]
    image = image.astype(np.float32, copy=False)
    image -= 127.5
    image /= 127.5
    return torch.from_numpy(image)


def to_feature_vector(vector):
    array_2d = (
        vector if isinstance(vector, np.ndarray) else vector.detach().cpu().numpy()
    )
    return np.hstack((array_2d[::2], array_2d[1::2]))


def download_weights(path: pathlib, url):
    import requests
    import tqdm

    if path.exists():
        return
    response = requests.get(url, stream=True)
    weights = []
    with tqdm.tqdm(
        desc=(path).as_posix(),
        total=int(response.headers.get("content-length", 0)),
        unit="iB",
        unit_scale=True,
        unit_divisor=1024,
    ) as progressbar:
        for chunk in response.iter_content(chunk_size=1024):
            weights += [chunk]
            progressbar.update(len(chunk))
    with open(path, mode="wb") as f:
        *map(f.write, weights),


def cv2_to_mp(image: np.ndarray):
    import mediapipe as mp

    return mp.Image(
        image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    )
