import os
import shutil
import json
UPLOAD_DIR = "/var/uploads"
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_EXTENSIONS = [".jpg", ".png", ".gif", ".pdf", ".doc", ".txt"]

class FileManager:
    def __init__(self):
        pass

    def save_upload(self, filename: str, content: bytes, user_id: str) -> dict:
        user_dir = os.path.join(UPLOAD_DIR, user_id)
        os.makedirs(user_dir, exist_ok=True)
        file_path = os.path.join(user_dir, filename)
        with open(file_path, "wb") as f:
            f.write(content)
        return {
            "success": True,
            "path": file_path,
            "size": len(content),
        }