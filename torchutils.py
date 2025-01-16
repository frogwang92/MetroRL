from enum import Enum
from typing import Dict, List, Sequence, Tuple, Union

import numpy as np
import torch
from torch import Tensor

def override(cls):
    """Decorator for documenting method overrides."""

    def check_override(method):
        if method.__name__ not in dir(cls):
            raise NameError("{} does not override any method of {}".format(method, cls))
        return method

    return check_override

class TorchUtils:
    @staticmethod
    def clamp_with_norm(tensor: Tensor, max_norm: float):
        norm = torch.linalg.vector_norm(tensor, dim=-1)
        new_tensor = (tensor / norm.unsqueeze(-1)) * max_norm
        cond = (norm > max_norm).unsqueeze(-1).expand(tensor.shape)
        tensor = torch.where(cond, new_tensor, tensor)
        return tensor

    @staticmethod
    def rotate_vector(vector: Tensor, angle: Tensor):
        if len(angle.shape) == len(vector.shape):
            angle = angle.squeeze(-1)

        assert vector.shape[:-1] == angle.shape
        assert vector.shape[-1] == 2

        cos = torch.cos(angle)
        sin = torch.sin(angle)
        return torch.stack(
            [
                vector[..., X] * cos - vector[..., Y] * sin,
                vector[..., X] * sin + vector[..., Y] * cos,
            ],
            dim=-1,
        )

    @staticmethod
    def cross(vector_a: Tensor, vector_b: Tensor):
        return (
            vector_a[..., X] * vector_b[..., Y] - vector_a[..., Y] * vector_b[..., X]
        ).unsqueeze(-1)

    @staticmethod
    def compute_torque(f: Tensor, r: Tensor) -> Tensor:
        return TorchUtils.cross(r, f)

    @staticmethod
    def to_numpy(data: Union[Tensor, Dict[str, Tensor], List[Tensor]]):
        if isinstance(data, Tensor):
            return data.cpu().detach().numpy()
        elif isinstance(data, Dict):
            return {key: TorchUtils.to_numpy(value) for key, value in data.items()}
        elif isinstance(data, Sequence):
            return [TorchUtils.to_numpy(value) for value in data]
        else:
            raise NotImplementedError(f"Invalid type of data {data}")

    @staticmethod
    def recursive_clone(value: Union[Dict[str, Tensor], Tensor]):
        if isinstance(value, Tensor):
            return value.clone()
        else:
            return {key: TorchUtils.recursive_clone(val) for key, val in value.items()}

    @staticmethod
    def recursive_require_grad_(value: Union[Dict[str, Tensor], Tensor, List[Tensor]]):
        if isinstance(value, Tensor) and torch.is_floating_point(value):
            value.requires_grad_(True)
        elif isinstance(value, Dict):
            for val in value.values():
                TorchUtils.recursive_require_grad_(val)
        else:
            for val in value:
                TorchUtils.recursive_require_grad_(val)

    @staticmethod
    def where_from_index(env_index, new_value, old_value):
        mask = torch.zeros_like(old_value, dtype=torch.bool, device=old_value.device)
        mask[env_index] = True
        return torch.where(mask, new_value, old_value)

