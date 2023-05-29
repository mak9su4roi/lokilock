import numpy as np


def cosine_similarity(x1, x2):
    return np.dot(x1, x2.T) / (np.linalg.norm(x1) * np.linalg.norm(x2))
