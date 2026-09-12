import os

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from ..uploads import UPLOAD_DIR

router = APIRouter(prefix="/api/files", tags=["files"])


@router.get("/{stored_name}")
def get_file(stored_name: str):
    path = os.path.join(UPLOAD_DIR, stored_name)
    if not os.path.abspath(path).startswith(os.path.abspath(UPLOAD_DIR)) or not os.path.exists(path):
        raise HTTPException(404, "File not found")
    return FileResponse(path)
