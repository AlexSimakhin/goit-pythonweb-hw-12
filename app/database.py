"""
Database configuration and connection setup for the Contacts REST API.
Loads environment variables and initializes SQLAlchemy engine, session, and base class.
"""

import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Detect pytest early and force test env
IS_PYTEST = any('pytest' in arg for arg in sys.argv)
ENV_TEST_PATH = os.path.join(
    os.path.dirname(__file__), '..', '.env.test'
)
if IS_PYTEST or os.environ.get('TESTING') == '1':
    load_dotenv(
        dotenv_path=ENV_TEST_PATH,
        override=True,
    )
    os.environ['TESTING'] = '1'
else:
    load_dotenv()


if IS_PYTEST or os.environ.get('TESTING') == '1':
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./test.db')
else:
    DATABASE_URL = os.getenv(
        'DATABASE_URL',
        'postgresql://user:password@localhost:5433/contacts_db',
    )

# Only set engine/SessionLocal to None if building docs
if os.environ.get("READTHEDOCS") == "True" or os.environ.get("SPHINX_BUILD") == "True":
    engine = None  # pylint: disable=invalid-name
    SessionLocal = None  # pylint: disable=invalid-name
else:
    engine = create_engine(DATABASE_URL)  # pylint: disable=invalid-name
    SessionLocal = sessionmaker(  # pylint: disable=invalid-name
        autocommit=False, autoflush=False, bind=engine
    )
Base = declarative_base()
"""Declarative base class used by SQLAlchemy models throughout the project."""
