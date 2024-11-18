from datetime import datetime, timezone
from xmlrpc.client import DateTime

from asyncpg.pgproto.pgproto import timedelta
from fastapi import Depends, Response, APIRouter
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import get_db


router = APIRouter(prefix="/email", tags=["email"])


@router.get('/{username}')
async def email_status(username: str, response: Response, db: AsyncSession = Depends(get_db)):
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
