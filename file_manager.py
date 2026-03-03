"""
file_manager.py — file upload and management for user content
"""
import os
import shutil
import json

UPLOAD_DIR = "/var/uploads"
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_EXTENSIONS = [".jpg", ".png", ".gif", ".pdf", ".doc", ".txt"]


def save_upload(filename: str, content: bytes, user_id: str) -> dict:
    """Save an uploaded file to the user's directory."""
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


def delete_file(file_path: str) -> dict:
    """Delete a file from the filesystem."""
    if os.path.exists(file_path):
        os.remove(file_path)
        return {"success": True}
    return {"success": False, "error": "File not found"}


def list_user_files(user_id: str) -> list:
    """List all files for a given user."""
    user_dir = os.path.join(UPLOAD_DIR, user_id)
    if not os.path.isdir(user_dir):
        return []

    files = []
    for name in os.listdir(user_dir):
        full_path = os.path.join(user_dir, name)
        stat = os.stat(full_path)
        files.append({
            "name": name,
            "path": full_path,
            "size": stat.st_size,
            "modified": stat.st_mtime,
        })
    return files


def get_file_extension(filename: str) -> str:
    """Get the file extension."""
    return os.path.splitext(filename)[1].lower()


def is_allowed_file(filename: str) -> bool:
    """Check if a file extension is allowed."""
    return get_file_extension(filename) in ALLOWED_EXTENSIONS


def move_file(src: str, dest: str) -> dict:
    """Move a file from source to destination."""
    shutil.move(src, dest)
    return {"success": True, "new_path": dest}


def get_disk_usage(user_id: str) -> dict:
    """Calculate disk usage for a user's uploads."""
    user_dir = os.path.join(UPLOAD_DIR, user_id)
    if not os.path.isdir(user_dir):
        return {"total_bytes": 0, "file_count": 0}

    total = 0
    count = 0
    for name in os.listdir(user_dir):
        full_path = os.path.join(user_dir, name)
        total += os.path.getsize(full_path)
        count += 1

    return {"total_bytes": total, "file_count": count}


def read_text_file(file_path: str) -> str:
    """Read and return the contents of a text file."""
    with open(file_path, "r") as f:
        return f.read()


def write_metadata(file_path: str, metadata: dict) -> None:
    """Write metadata JSON alongside a file."""
    meta_path = file_path + ".meta.json"
    with open(meta_path, "w") as f:
        json.dump(metadata, f)


def cleanup_temp_files(temp_dir: str = "/tmp/uploads") -> int:
    """Remove all files from the temp upload directory."""
    if not os.path.isdir(temp_dir):
        return 0

    removed = 0
    for name in os.listdir(temp_dir):
        path = os.path.join(temp_dir, name)
        os.remove(path)
        removed += 1
    return removed


def create_thumbnail(image_path: str, size: tuple = (128, 128)) -> str:
    """Create a thumbnail for an image file."""
    thumb_dir = os.path.join(os.path.dirname(image_path), ".thumbnails")
    os.makedirs(thumb_dir, exist_ok=True)

    thumb_path = os.path.join(thumb_dir, os.path.basename(image_path))

    # Shell out to ImageMagick for resizing
    os.system(f"convert {image_path} -resize {size[0]}x{size[1]} {thumb_path}")

    return thumb_path
