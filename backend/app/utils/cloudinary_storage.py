"""Cloudinary upload/delete helpers for ultrasound images."""

from __future__ import annotations

from typing import Dict, Any
import cloudinary
import cloudinary.uploader
import cloudinary.utils

from app.core.config import (
    CLOUDINARY_API_KEY,
    CLOUDINARY_API_SECRET,
    CLOUDINARY_CLOUD_NAME,
    CLOUDINARY_FOLDER,
)


def is_cloudinary_configured() -> bool:
    """Return True when required Cloudinary settings are available."""
    return bool(CLOUDINARY_CLOUD_NAME and CLOUDINARY_API_KEY and CLOUDINARY_API_SECRET)


def configure_cloudinary() -> None:
    """Configure cloudinary SDK once per process call site."""
    cloudinary.config(
        cloud_name=CLOUDINARY_CLOUD_NAME,
        api_key=CLOUDINARY_API_KEY,
        api_secret=CLOUDINARY_API_SECRET,
        secure=True,
    )


def upload_ultrasound_image(file_obj, patient_identifier: str, visit_id: int, filename: str) -> Dict[str, Any]:
    """Upload a single ultrasound image and return normalized metadata."""
    if not is_cloudinary_configured():
        raise ValueError("Cloudinary is not configured")

    configure_cloudinary()
    folder = f"{CLOUDINARY_FOLDER}/patient_{patient_identifier}/visit_{visit_id}"

    upload_result = cloudinary.uploader.upload(
        file_obj,
        folder=folder,
        resource_type="image",
        use_filename=True,
        unique_filename=True,
        overwrite=False,
    )

    public_id = upload_result.get("public_id")
    thumb_url, _ = cloudinary.utils.cloudinary_url(
        public_id,
        secure=True,
        width=320,
        height=320,
        crop="fill",
        gravity="auto",
        fetch_format="auto",
        quality="auto",
    )

    return {
        "public_id": public_id,
        "secure_url": upload_result.get("secure_url"),
        "thumbnail_url": thumb_url,
        "file_name": filename,
        "format": upload_result.get("format"),
        "bytes": upload_result.get("bytes"),
        "width": upload_result.get("width"),
        "height": upload_result.get("height"),
    }


def delete_ultrasound_image(public_id: str) -> None:
    """Delete an ultrasound image from Cloudinary by public_id."""
    if not is_cloudinary_configured() or not public_id:
        return

    configure_cloudinary()
    cloudinary.uploader.destroy(public_id, resource_type="image", invalidate=True)
