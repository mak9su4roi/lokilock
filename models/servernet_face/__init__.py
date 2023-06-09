import pathlib
from typing import Callable, Union, Optional

import numpy as np
import torch

from common.types.vector import Vector

from .. import load as _load
from ..metrics import cosine_similarity
from ..utils import download_weights, to_feature_vector
from .model import ServerFace



POINTS = pathlib.Path(__file__).parent / "points.pts"
POINTS_URL = "https://www.dropbox.com/s/48r6cyshsz6oh8w/points.pts?dl=1"


def recognize(
    fw: np.ndarray,
    dataset: dict[str, list[Vector]],
    similarity_th: float = 0.35,
) -> tuple[float, str]:
    res = max(
        [
            {
                "user": name,
                "confidence": np.mean(
                    np.array([cosine_similarity(fw, v.data) for v in vectors])
                    > similarity_th
                ),
            }
            for name, vectors in dataset.items()
        ],
        key=lambda pair: pair["confidence"],
    )
    return res["confidence"], res["user"]


def initializer(use_se=False, **kwargs):
    return torch.nn.DataParallel(ServerFace(use_se=use_se, **kwargs))


def load(
    initializer: Callable = initializer,
    device: Optional[torch.DeviceObjType] = None,
    points: pathlib.Path = POINTS,
    **kwargs
) -> Callable[[Union[Vector, torch.Tensor, np.ndarray]], np.ndarray]:
    download_weights(POINTS, POINTS_URL)
    model = _load(
        model=initializer(**kwargs),
        device=device or torch.device("cuda" if torch.cuda.is_available() else "cpu"),
        points=points,
    )

    def execute(data):
        if isinstance(data, np.ndarray):
            tensor = torch.from_numpy(data)
        elif isinstance(data, Vector):
            tensor = data.tensor
        elif isinstance(data, torch.Tensor):
            tensor = data
        return to_feature_vector(model(tensor))

    return execute
