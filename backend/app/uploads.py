import os
import uuid
from fastapi import UploadFile

from .database import DATA_DIR

UPLOAD_DIR = os.path.join(DATA_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


async def save_upload(file: UploadFile | None) -> str | None:
    if file is None or not file.filename:
        return None
    ext = os.path.splitext(file.filename)[1]
    stored_name = f"{uuid.uuid4().hex}{ext}"
    dest_path = os.path.join(UPLOAD_DIR, stored_name)
    with open(dest_path, "wb") as out:
        out.write(await file.read())
    return stored_name


def delete_upload(stored_name: str | None) -> None:
    if not stored_name:
        return
    path = os.path.join(UPLOAD_DIR, stored_name)
    if os.path.exists(path):
        os.remove(path)
