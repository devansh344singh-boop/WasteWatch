"""Image preparation helpers. Add model-specific transforms only with a trained model."""
from pathlib import Path
from PIL import Image, ImageOps

def load_rgb(path: str | Path) -> Image.Image:
    with Image.open(path) as source:
        return ImageOps.exif_transpose(source).convert("RGB")
