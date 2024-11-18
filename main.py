from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.contacts import routes_users as contacts_routes
from src.contacts import routes_admin as contacts_admin_routes
from src.services.health_checker import health_checker
from src.services.email_status_track import routes_email_status
from src.users import routes as users_routes

app = FastAPI()

app.mount("/static", StaticFiles(directory='src/static'), name="static")
app.include_router(users_routes.router, prefix="/api")
app.include_router(contacts_admin_routes.router, prefix="/api")
app.include_router(contacts_routes.router, prefix="/api")
app.include_router(health_checker.router, prefix="/api")
app.include_router(routes_email_status.router, prefix="/api")

app.add_middleware(
    CORSMiddleware,  # type: ignore
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get('/')
def index():
    return {"message": "Contacts Application"}
