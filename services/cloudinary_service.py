"""
Cloudinary Service — thin wrapper for cloud file storage.
All uploaded files (student photos, documents, certificates, resumes) are
stored here instead of the local filesystem so they survive redeploys.
"""
import cloudinary
import cloudinary.uploader
import cloudinary.api
from flask import current_app


def _init_cloudinary():
    """Configure cloudinary from Flask app config."""
    cloudinary.config(
        cloud_name=current_app.config.get('CLOUDINARY_CLOUD_NAME', ''),
        api_key=current_app.config.get('CLOUDINARY_API_KEY', ''),
        api_secret=current_app.config.get('CLOUDINARY_API_SECRET', ''),
        secure=True,
    )


def upload_file(file_stream, folder: str = 'edutrack', resource_type: str = 'auto') -> tuple[str, str]:
    """
    Upload a file stream to Cloudinary.

    Args:
        file_stream: werkzeug FileStorage or any file-like object.
        folder:       Cloudinary folder name (e.g. 'edutrack/photos').
        resource_type: 'image', 'raw', or 'auto' (auto-detects).

    Returns:
        (secure_url, public_id) tuple — store both in the DB.
        secure_url  → use as <img src> or download link.
        public_id   → needed to delete the file later.
    """
    _init_cloudinary()
    result = cloudinary.uploader.upload(
        file_stream,
        folder=folder,
        resource_type=resource_type,
        overwrite=True,
    )
    return result['secure_url'], result['public_id']


def delete_file(public_id: str, resource_type: str = 'image') -> bool:
    """
    Delete a file from Cloudinary by its public_id.

    Args:
        public_id:     The public_id returned at upload time.
        resource_type: Must match the type used at upload ('image' or 'raw').

    Returns:
        True if deleted successfully, False otherwise.
    """
    if not public_id:
        return False
    _init_cloudinary()
    try:
        result = cloudinary.uploader.destroy(public_id, resource_type=resource_type)
        return result.get('result') == 'ok'
    except Exception:
        return False


def get_resource_type(file_type: str) -> str:
    """
    Map our file_type category to a Cloudinary resource_type.

    'photo'       → 'image'
    everything else → 'raw'  (PDFs, Word docs, etc.)
    """
    return 'image' if file_type == 'photo' else 'raw'
