"""Lazy model loader seam; no weights are bundled or downloaded by default."""
from functools import lru_cache
from pathlib import Path
import os

@lru_cache(maxsize=1)
def load_model():
    model_path = os.getenv("WASTE_CLASSIFIER_MODEL")
    if not model_path:
        return None
    path = Path(model_path)
    if not path.is_file():
        raise FileNotFoundError(f"Configured classifier model does not exist: {path}")
    # Import torch only when a model is configured so normal API startup stays lightweight.
    import torch
    return torch.jit.load(str(path), map_location="cpu").eval()
