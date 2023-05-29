import pathlib

import torch


def load(model: torch.nn.Module, points: pathlib.Path, device: torch.DeviceObjType):
    model.load_state_dict(torch.load(points, map_location=device))
    model.eval()
    return model
