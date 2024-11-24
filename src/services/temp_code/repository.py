import random
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.temp_code.model import TemporaryCode


async def get_temp_code(email: str, temp_code: str, db: AsyncSession) -> TemporaryCode:
    stmt = select(TemporaryCode).where(TemporaryCode.temp_code == temp_code, TemporaryCode.user_email == email)
    result = await db.execute(stmt)
    result = result.scalar_one_or_none()
    return result

async def update_temp_code(temp_code: TemporaryCode, db: AsyncSession):
    temp_code.used_at = datetime.now()
    await db.commit()

async def create_temp_code(email: str, db: AsyncSession, description: str) -> TemporaryCode:
    generated_temp_code = f"{random.randint(0, 999999):06d}"
    temp_code = TemporaryCode(temp_code=generated_temp_code, description=f'{description}', user_email=email)
    db.add(temp_code)
    await db.commit()
    await db.refresh(temp_code)
    return temp_code
