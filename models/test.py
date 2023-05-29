import pathlib
from time import perf_counter_ns

import numpy as np
import torch

from common.types.vector import Vector
from models import edgenet_face, resnet_face, servernet_face, utils

ITERATIONS = 100


def update_points(superset, *subsets):
    super = superset.load()
    for subset in subsets:
        sub = subset.initializer()
        points = subset.POINTS
        print(f"{points=}")
        torch.save(
            {k: v for k, v in super.state_dict().items() if k in sub.state_dict()},
            points,
        )


def size(tensor):
    return tensor.element_size() * tensor.nelement()


update_points(resnet_face, servernet_face, edgenet_face)

rn = resnet_face.load(device=torch.device("cpu"))
sn = servernet_face.load(device=torch.device("cpu"))
en = edgenet_face.load(device=torch.device("cpu"))


def time_it(func, n=1):
    t = []
    for _ in range(n):
        t_ = perf_counter_ns()
        func()
        t += [perf_counter_ns() - t_]
    return np.mean(t) / 10**9


img = utils.load_image(pathlib.Path(__file__).parent / "sample.jpg")
rn_res = utils.to_feature_vector(rn(img))
en_res = en(img)
sn_res = sn(en_res)

assert np.all(
    rn_res == sn(Vector.from_tensor(en(img)))
), "Composition of split DNN poduce different results than undevided DNN"

rn_avg_t = time_it(lambda: rn(img), n=ITERATIONS)
en_avg_t = time_it(lambda: en(img), n=ITERATIONS)
sn_avg_t = time_it(lambda: sn(en_res), n=ITERATIONS)

en_np_size, img_np_size = (t.detach().cpu().numpy().size for t in [en_res, img])
print(f"expansion: {en_np_size/img_np_size=}")
print(f"avg_time:  {rn_avg_t=}, {en_avg_t=}, {sn_avg_t=}")
print(f"{rn_res.shape=}")
