import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

# The os.getenv command looks for the cloud database first. 
# If it fails (because you are on your local PC), it uses your local string instead!
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:LOCAL_PASSWORD@localhost:5432/astranova_db")

# Sometimes cloud providers use 'postgres://' but SQLAlchemy requires 'postgresql://'
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()