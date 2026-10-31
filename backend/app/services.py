from pathlib import Path
from uuid import uuid4
from fastapi import HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError
from .config import settings

class ImageStorage:
    allowed = {"JPEG": ".jpg", "PNG": ".png", "WEBP": ".webp"}
    async def save(self, upload: UploadFile) -> str:
        data = await upload.read(settings.max_upload_mb * 1024 * 1024 + 1)
        if not data: raise HTTPException(400, "Image is empty")
        if len(data) > settings.max_upload_mb * 1024 * 1024: raise HTTPException(413, "Image exceeds the 8 MB limit")
        try:
            import io
            image = Image.open(io.BytesIO(data)); image.verify()
            fmt = image.format
            if image.width * image.height > 40_000_000: raise HTTPException(413, "Image dimensions are too large")
        except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError): raise HTTPException(400, "File is not a valid image")
        if fmt not in self.allowed: raise HTTPException(415, "Use a JPEG, PNG, or WebP image")
        directory = Path(settings.upload_dir).resolve(); directory.mkdir(parents=True, exist_ok=True)
        name = f"{uuid4().hex}{self.allowed[fmt]}"; (directory / name).write_bytes(data)
        return name
    def delete(self, name: str):
        path = (Path(settings.upload_dir).resolve() / Path(name).name).resolve()
        if path.parent == Path(settings.upload_dir).resolve() and path.exists(): path.unlink()

image_storage = ImageStorage()

class WasteClassifier:
    """Future classifier adapter. Deliberately returns no invented prediction."""
    def predict(self, image_path: str) -> dict:
        return {"predicted_category": None, "confidence_score": None, "ai_status": "not_configured", "requires_human_review": True}

ai_service = WasteClassifier()
