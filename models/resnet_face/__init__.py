import pathlib
from typing import Callable, Optional

import torch

from .. import load as _load
from ..blocks import IRBlock
from ..utils import download_weights
from .model import ResNetFace

POINTS_URL = "https://www.dropbox.com/s/1gd3w9vohh6oe2e/points.pts?dl=1"
POINTS = pathlib.Path(__file__).parent / "points.pts"


def initializer(use_se=False, **kwargs):
    return torch.nn.DataParallel(
        ResNetFace(IRBlock, [2, 2, 2, 2], use_se=use_se, **kwargs)
    )


def load(
    initializer: Callable = initializer,
    device: Optional[torch.DeviceObjType] = None,
    **kwargs
):
    download_weights(POINTS, POINTS_URL)
    return _load(
        model=initializer(**kwargs),
        device=device or torch.device("cuda" if torch.cuda.is_available() else "cpu"),
        points=POINTS,
    )
