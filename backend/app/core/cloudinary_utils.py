import cloudinary
import cloudinary.uploader
from app.core.config import (
    CLOUDINARY_CLOUD_NAME,
    CLOUDINARY_API_KEY,
    CLOUDINARY_API_SECRET,
    CLOUDINARY_FOLDER
)

# Configure Cloudinary
cloudinary.config(
    cloud_name=CLOUDINARY_CLOUD_NAME,
    api_key=CLOUDINARY_API_KEY,
    api_secret=CLOUDINARY_API_SECRET,
    secure=True
)


def upload_image_to_cloudinary(file_path: str, public_id: str = None) -> str:
    """
    Upload image to Cloudinary and return the URL
    """
    result = cloudinary.uploader.upload(
        file_path,
        folder=CLOUDINARY_FOLDER,
        public_id=public_id,
        resource_type="image"
    )

    return result["secure_url"]