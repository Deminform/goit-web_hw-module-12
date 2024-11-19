from contextlib import asynccontextmanager
from ipaddress import ip_address
from typing import Callable

from pathlib import Path
import redis.asyncio as redis
from fastapi import FastAPI, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi_limiter import FastAPILimiter
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from src.contacts import routes_users as contacts_routes
from src.contacts import routes_admin as contacts_admin_routes
from src.services.health_checker import health_checker
from src.services.email_status_track import routes_email_status
from src.services.auth import routes as auth_routes
from src.users import routes as users_routes
from conf.config import app_config

banned_ips = []
templates = Jinja2Templates(directory="src/templates")
rootdir = Path(__file__).parent

@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    r = redis.Redis(
        host=app_config.REDIS_DOMAIN,
        port=app_config.REDIS_PORT,
        decode_responses=True,
        password=app_config.REDIS_PASSWORD,
        db=0,
    )
    await FastAPILimiter.init(r)

    yield

    await r.close()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,  # type: ignore
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.mount("/static", StaticFiles(directory="src/static"), name="static")
app.include_router(auth_routes.router, prefix="/api")
app.include_router(users_routes.router, prefix="/api")
app.include_router(contacts_admin_routes.router, prefix="/api")
app.include_router(contacts_routes.router, prefix="/api")
app.include_router(health_checker.router, prefix="/api")
app.include_router(routes_email_status.router, prefix="/api")


@app.middleware('http')
async def black_list(request: Request, call_next: Callable):
    ip = ip_address(request.client.host)
    if ip in banned_ips:
        return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={'detail': 'You are banned'})
    response = await call_next(request)
    return response


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse('index.html', {'request': request, 'page_title': 'Python Test Landing Page'})
