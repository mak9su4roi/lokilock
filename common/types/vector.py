import pathlib
from typing import TYPE_CHECKING

import numpy as np
from pydantic import validator

from .model import Model

if TYPE_CHECKING:
    import torch


class Vector(Model):
    data: np.ndarray

    @validator("data", pre=True)
    def _(cls, val):
        return cls.to_numpy(val) if isinstance(val, dict) else val

    @property
    def tensor(self):
        import torch

        return torch.from_numpy(self.data)

    @classmethod
    def from_tensor(cls, src: "torch.Tensor"):
        return cls(data=src.detach().cpu().numpy())

    def to_file(self, dst: pathlib.Path):
        return np.save(dst, self.data)

    @classmethod
    def from_file(cls, src: pathlib.Path):
        return cls(data=np.load(src))
