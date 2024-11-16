from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.middleware.cors import CORSMiddleware

from database.db import get_db
from src.contacts import routes_users as contacts_routes
from src.contacts import routes_admin as contacts_admin_routes
from src.users import routes as users_routes

app = FastAPI()
app.include_router(users_routes.router, prefix="/api")
app.include_router(contacts_admin_routes.router, prefix="/api")
app.include_router(contacts_routes.router, prefix="/api")

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


@app.get('/api/healthchecker')
async def healthcheck(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(text("SELECT 1"))
        result = result.fetchone()
        if result is None:
            raise HTTPException(status_code=500, detail="Database is not configured correctly")
        return {"message": "Database is healthy"}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Error connecting to the database")
