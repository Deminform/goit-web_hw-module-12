from sqlalchemy import String, DateTime, func, Integer, ForeignKey
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.testing.pickleable import User

from conf.config import Base


class Contact(Base):
    __tablename__ = 'contacts'
    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    phone: Mapped[str] = mapped_column(String(10), nullable=False, unique=True)
    birthday: Mapped[DateTime] = mapped_column(DateTime, nullable=True)
    description: Mapped[str] = mapped_column(String(300), nullable=True)

    created_at: Mapped[DateTime] = mapped_column('created_at', DateTime, nullable=True, default=func.now())
    updated_at: Mapped[DateTime] = mapped_column('updated_at', DateTime, nullable=True, default=func.now(),
                                                 onupdate=func.now())
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=True)
    user: Mapped['User'] = relationship('User', backref='contacts', lazy='joined')

    @hybrid_property
    def fullname(self):
        return f'{self.first_name} {self.last_name}'

    @fullname.expression
    def fullname(cls) -> str:
        return func.concat(cls.first_name, ' ', cls.last_name)
