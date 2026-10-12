
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


# Project folders:
# GZUVotingGitHub/
#   Backend/
#   Blockchain/.env
#
# Local development:
#   Load Blockchain/.env if it exists.
#
# Render deployment:
#   Use environment variables configured in the Render dashboard.

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
ENV_FILE = PROJECT_DIR / "Blockchain" / ".env"

# Load local environment configuration when available.
# Do not require a local .env file in production.
if ENV_FILE.is_file():
    load_dotenv(ENV_FILE, override=False)

# Read the database connection string from the environment.
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is missing. Set it in the deployment "
        "environment or provide it in the local Blockchain/.env file."
    )

# Normalize PostgreSQL URLs to use psycopg v3.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgres://",
        "postgresql+psycopg://",
        1,
    )
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgresql://",
        "postgresql+psycopg://",
        1,
    )

# This application expects PostgreSQL with the psycopg v3 driver.
if not DATABASE_URL.startswith("postgresql+psycopg://"):
    raise RuntimeError(
        "Invalid DATABASE_URL. Expected a PostgreSQL URL "
        "using the psycopg v3 driver."
    )

# Create the database engine.
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    connect_args={"connect_timeout": 15},
)

# Create database sessions.
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# Base class for SQLAlchemy models.
Base = declarative_base()
