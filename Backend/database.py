
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


# Project folders:
# GZUVotingGitHub/
#   Backend/
#   Blockchain/.env

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
ENV_FILE = PROJECT_DIR / "Blockchain" / ".env"

if not ENV_FILE.is_file():
    raise FileNotFoundError(
        f"Database configuration file not found: {ENV_FILE}"
    )

load_dotenv(ENV_FILE, override=False)

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        f"DATABASE_URL is missing from {ENV_FILE}"
    )

# Use the installed psycopg v3 driver.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgres://", "postgresql+psycopg://", 1
    )
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgresql://", "postgresql+psycopg://", 1
    )

if not DATABASE_URL.startswith("postgresql+psycopg://"):
    raise RuntimeError(
        "Expected a PostgreSQL DATABASE_URL using psycopg."
    )

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    connect_args={"connect_timeout": 15},
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()
