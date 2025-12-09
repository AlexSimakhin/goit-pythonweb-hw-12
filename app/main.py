"""
Main entry point for the FastAPI Contacts REST API application.
Initializes the database tables and includes the contacts router.
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import Base, engine
from app.routers import contact, user

# During local testing (pytest) create tables automatically to simplify setup.
if not os.environ.get("READTHEDOCS") and not os.environ.get("SPHINX_BUILD"):
    if engine is not None and os.environ.get('TESTING') == '1':
        Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Contacts REST API",
    description="API for managing contacts",
    version="1.0.0",
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
