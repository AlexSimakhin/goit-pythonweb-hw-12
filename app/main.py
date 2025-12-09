"""
Main entry point for the FastAPI Contacts REST API application.
Initializes the database tables and includes the contacts router.
"""
import os
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import OperationalError
from app.database import Base, engine
from app.routers import contact, user

# During local testing (pytest) create tables automatically to simplify setup.
if not os.environ.get("READTHEDOCS") and not os.environ.get("SPHINX_BUILD"):
    if engine is not None and os.environ.get('TESTING') == '1':
        Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Skip when building docs or when running tests (tests handle their own setup)
    if not (os.environ.get("READTHEDOCS") or os.environ.get("SPHINX_BUILD")):
        if os.environ.get('TESTING') != '1' and engine is not None:
            # Retry a few times in case DB is not immediately reachable
            for _ in range(10):
                try:
                    Base.metadata.create_all(bind=engine)
                    break
                except OperationalError:
                    time.sleep(2)
    yield

app = FastAPI(
    title="Contacts REST API",
    description="API for managing contacts",
    version="1.0.0",
    lifespan=lifespan,
)
"""FastAPI application instance for the Contacts REST API."""

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register the contacts router providing CRUD endpoints under /contacts.
app.include_router(contact.router)
# Register the users router providing auth and profile endpoints under /users.
app.include_router(user.router)
