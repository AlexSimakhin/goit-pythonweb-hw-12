"""
Main entry point for the FastAPI Contacts REST API application.
Initializes the database tables and includes the contacts router.
"""

from fastapi import FastAPI
from database import Base, engine
from routers import contacts

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Contacts REST API", description="API for managing contacts", version="1.0.0")

app.include_router(contacts.router)
