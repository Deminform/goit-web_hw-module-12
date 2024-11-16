import os
from dotenv import load_dotenv

from sqlalchemy.orm import DeclarativeBase


load_dotenv()
user = os.getenv("USER")
password = os.getenv("PASSWORD")
dbname = os.getenv("DBNAME")
host = os.getenv("HOST")
port = os.getenv("PORT")

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

TOKEN_LIFETIME = 15
REFRESH_TOKEN_LIFETIME = 7


class Base(DeclarativeBase):
    pass

class Config:
    DB_URL = f'postgresql+asyncpg://{user}:{password}@{host}:{port}/{dbname}'

db_config = Config


