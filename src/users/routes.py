import uuid
from pathlib import Path

import cloudinary
import cloudinary.uploader
from fastapi import Depends, APIRouter, UploadFile, File
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession

from src.users import repository as user_repository
from conf.config import app_config
from database.db import get_db
from src.users.models import User
from src.users.schemas import UserResponseSchema
from src.services.auth.jwt_auth import auth_service

router = APIRouter(prefix="/users", tags=["users"])
cloudinary.config(
    cloud_name=app_config.CLOUDINARY_NAME,
    api_key=app_config.CLOUDINARY_API_KEY,
    api_secret=app_config.CLOUDINARY_API_SECRET,
    secure=True,
)


@router.get('/me', response_model=UserResponseSchema, dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def get_current_user(user: User = Depends(auth_service.get_current_user)):
    """
    Get the current authenticated user's details.

    This endpoint allows the current authenticated user to retrieve their own user details.

    :param user: The current authenticated user, automatically injected by dependency.
    :type user: User

    :return: The current authenticated user's details.
    :rtype: User
    """
    return user


@router.patch('/avatar', response_model=UserResponseSchema, dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def get_current_user(file: UploadFile = File(),
                           user: User = Depends(auth_service.get_current_user),
                           db: AsyncSession = Depends(get_db)):
    """
    Update the current authenticated user's avatar.

    This endpoint allows the current authenticated user to update their avatar by uploading a new image file.
    The image is uploaded to Cloudinary, and the public URL is updated in the user's profile.

    :param file: The new avatar image file to be uploaded.
    :type file: UploadFile
    :param user: The current authenticated user, automatically injected by dependency.
    :type user: User
    :param db: The asynchronous database session, automatically injected by dependency.
    :type db: AsyncSession

    :return: The updated user details with the new avatar URL.
    :rtype: User
    """
    ext = Path(file.filename).suffix.lower()
    unique_filename = uuid.uuid4().hex
    res = cloudinary.uploader.upload(file.file, public_id=unique_filename, overwrite=True, folder=app_config.CLOUDINARY_FOLDER)
    full_public_id = res.get('public_id')
    res_url = cloudinary.CloudinaryImage(full_public_id + ext).build_url(
        width=200,
        height=200,
        crop='fill',
        version=res.get('version')
    )
    user = await user_repository.update_avatar_url(user.email, res_url, db)
    return user



