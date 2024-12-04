from datetime import datetime, timedelta

from pydantic import EmailStr
from sqlalchemy import String, DateTime, func, Integer, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from conf.config import Base, app_config


class TemporaryCode(Base):
    __tablename__ = 'temporary_codes'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    temp_code: Mapped[str] = mapped_column(String(6), nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    user_email: Mapped[str] = mapped_column(String(150), nullable=False)
    created_at: Mapped[datetime] = mapped_column('created_at', DateTime, default=datetime.now(), nullable=False)
    expires_at: Mapped[datetime] = mapped_column('expires_at', DateTime,
                                                 default=datetime.now() + timedelta(minutes=app_config.TEMP_CODE_LIFETIME),
                                                 nullable=False)
    used_at: Mapped[datetime] = mapped_column('used_at', DateTime, default=None, nullable=True)
