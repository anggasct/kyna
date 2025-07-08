from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import get_config

Base = declarative_base()

class DatabaseManager:
    def __init__(self):
        self.config = get_config()
        self.engine = create_engine(
            self.config.database.url,
            connect_args={"check_same_thread": False} if "sqlite" in self.config.database.url else {}
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def get_session(self):
        return self.SessionLocal()
    
    def create_tables(self):
        Base.metadata.create_all(bind=self.engine)

db_manager = DatabaseManager()

def get_db():
    db = db_manager.get_session()
    try:
        yield db
    finally:
        db.close()