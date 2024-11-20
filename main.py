import logging
import re
from contextlib import asynccontextmanager
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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("uvicorn.error")

user_agent_ban_list = []
templates = Jinja2Templates(directory="src/templates")
BASE_DIR = Path('.')

@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    try:
        r = redis.Redis(
            host=app_config.REDIS_DOMAIN,
            port=app_config.REDIS_PORT,
            decode_responses=True,
            password=app_config.REDIS_PASSWORD,
            db=0,
        )
        await FastAPILimiter.init(r)
        logger.info("FastAPILimiter is successfully connected to Redis..")
        yield
    except Exception as e:
        logger.error(f"Initialization error FastAPILimiter: {e}")
        raise
    finally:
        await r.close()
        logger.info("Connection to Redis closed.")

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,  # type: ignore
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.mount('/static', StaticFiles(directory=BASE_DIR / 'src' / 'static'), name="static")
app.include_router(auth_routes.router, prefix="/api")
app.include_router(users_routes.router, prefix="/api")
app.include_router(contacts_admin_routes.router, prefix="/api")
app.include_router(contacts_routes.router, prefix="/api")
app.include_router(health_checker.router, prefix="/api")
app.include_router(routes_email_status.router, prefix="/api")


@app.middleware('http')
async def user_agent_ban_middleware(request: Request, call_next: Callable):
    user_agent = request.headers.get('User-Agent', '')
    logger.info(f"A request has been received to {request.url} с User-Agent: {user_agent}")
    for ban_pattern in user_agent_ban_list:
        if re.search(ban_pattern, user_agent):
            logger.warning(f"Access Denied for User-Agent: {user_agent}")
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={'detail': 'You are banned'}
            )
    try:
        response = await call_next(request)
        logger.info(f"The request to {request.url} has been successfully processed with status {response.status_code}")
        return response
    except Exception as e:
        logger.error(f"Error processing the request to {request.url}: {e}")
        raise


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global error while processing the request to {request.url}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal Server Error"}
    )


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    logger.info(f"Home page request received: {request.url}")
    return templates.TemplateResponse('index.html', {'request': request, 'page_title': 'Python Test Landing Page'})
