import pathlib
from typing import Callable, Optional, Union

import numpy as np
import torch

from common.types.vector import Vector

from .. import load as _load
from ..blocks import IRBlock
from ..utils import download_weights, load_image
from .model import EdgeFace

POINTS = pathlib.Path(__file__).parent / "points.pts"
POINTS_URL = "https://www.dropbox.com/s/1p7om4rxcqlxzwa/points.pts?dl=1"


def initializer(use_se=False, **kwargs):
    return torch.nn.DataParallel(
        EdgeFace(block=IRBlock, layers=[2, 2, 2, 2], use_se=use_se, **kwargs),
    )


def load(
    initializer: Callable = initializer,
    device: Optional[torch.DeviceObjType] = None,
    points: pathlib.Path = POINTS,
    **kwargs
) -> Callable[[Union[np.ndarray, torch.Tensor, Vector]], torch.Tensor]:
    download_weights(POINTS, POINTS_URL)
    device_ = device or torch.device("cuda" if torch.cuda.is_available() else "cpu")

    model = _load(
        model= initializer(**kwargs),
        device=device_,
        points=points,
    )
    if device_ == torch.device("cpu"):
        model = model.module.to(device_)

    def execute(image):
        if isinstance(image, np.ndarray):
            tensor = load_image(image)
        elif isinstance(image, Vector):
            tensor = image.tensor
        elif isinstance(image, torch.Tensor):
            tensor = image
        return model(tensor)

    return execute
