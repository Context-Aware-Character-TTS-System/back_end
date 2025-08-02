import os
import aiofiles
from fastapi import UploadFile

async def save_upload_file(upload_file: UploadFile, destination_path: str):
    """
    Saves an uploaded file asynchronously to the specified destination path.
    """
    # Ensure the directory exists
    os.makedirs(os.path.dirname(destination_path), exist_ok=True)

    async with aiofiles.open(destination_path, "wb") as out_file:
        while content := await upload_file.read(1024):
            await out_file.write(content)
