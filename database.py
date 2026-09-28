

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "sqlite:///./chat.db"

# check_same_thread=False is needed because FastAPI can handle requests
# on different threads, and SQLite is normally strict about that.
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# SessionLocal is a "factory" that creates new database sessions when needed.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """
    This is a dependency FastAPI will call for every request that needs the DB.
    It opens a session, hands it to the request, and closes it afterwards -
    even if an error happens (that's what try/finally guarantees).
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
