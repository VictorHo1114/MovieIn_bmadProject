from .database import SessionLocal

def get_db():
    """
    FastAPI Dependency to get a DB session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()