from base64 import decodebytes, encodebytes

import numpy as np
from pydantic import BaseModel


class Model(BaseModel):
    @staticmethod
    def to_numpy(data: dict):
        return np.frombuffer(
            decodebytes(data["data"].encode()), dtype=data["type"]
        ).reshape(data["shape"])

    class Config:
        arbitrary_types_allowed = True
        validate_assignment = True
        json_encoders = {
            np.ndarray: lambda array: {
                "data": encodebytes(array.tobytes()).decode(),
                "type": str(array.dtype),
                "shape": array.shape,
            }
        }
