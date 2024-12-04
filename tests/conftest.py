import asyncio
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from fastapi_limiter.depends import RateLimiter

from conf.config import Base
from database.db import get_db
from main import app
from src.services.auth.jwt_auth import auth_service
from src.users.models import User, Role

SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool
)
TestingSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, expire_on_commit=False, bind=engine)

test_user = {'username': 'pacman', 'email': 'pacman@test.com', 'password': '000000'}


@pytest.fixture(scope="module", autouse=True)
def init_models_wrap():
    async def init_models():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        async with TestingSessionLocal() as session:
            hash_password = auth_service.get_password_hash(test_user['password'])
            current_user = User(
                username=test_user['username'],
                email=test_user['email'],
                password=hash_password,
                confirmed=True, role_id=3)
            role_guest = Role(name='guest')
            role_user = Role(name='user')
            role_admin = Role(name='admin')
            session.add(role_guest)
            session.add(role_user)
            session.add(role_admin)
            session.add(current_user)
            await session.commit()

    asyncio.run(init_models())

@pytest.fixture(scope="module")
def client():
    async def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session

        except Exception as err:
            await session.rollback()
            raise err
        finally:
            await session.close()

    app.dependency_overrides[get_db] = override_get_db

    yield TestClient(app)


@pytest_asyncio.fixture()
async def get_access_token():
    access_token = await auth_service.create_access_token(data={"sub": test_user['email']})
    return access_token

@pytest_asyncio.fixture()
async def redis_mock(monkeypatch):
    monkeypatch.setattr("fastapi_limiter.FastAPILimiter.redis", AsyncMock())
    monkeypatch.setattr("fastapi_limiter.FastAPILimiter.identifier", AsyncMock())
    monkeypatch.setattr("fastapi_limiter.FastAPILimiter.http_callback", AsyncMock())

@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_cache():
    FastAPICache.init(InMemoryBackend())
    yield
    await FastAPICache.clear()