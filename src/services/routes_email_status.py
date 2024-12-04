from datetime import datetime, timezone

from fastapi import Depends, Response, APIRouter
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import get_db

router = APIRouter(prefix="/email", tags=["email"])


@router.get('/{username}')
async def email_status(username: str, response: Response, db: AsyncSession = Depends(get_db)):
    """
    Tracks the email status for a given username by responding with an image.

    Args:
        username (str): The username for which the email status is being tracked.
        response (Response): The FastAPI Response object.
        db (AsyncSession): The database session dependency.

    Returns:
        FileResponse: An image file indicating that the email was opened.
    """
    print('-----------------------------------------------------------------------')
    print(f'Date / Time: {datetime.now(timezone.utc)} / {username} was opening an e-mail')
    print('-----------------------------------------------------------------------')

    headers = {
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "Expires": "0",
    }

    return FileResponse('src/static/open_check.png', media_type='image/png', headers=headers, content_disposition_type='inline'
    )
