from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import os

DB_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = f"sqlite:///{os.path.join(DB_DIR, 'roman_scribe.db')}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Note(Base):
    __tablename__ = "notes"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    content_raw = Column(Text)
    content_urdu = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class SmartTag(Base):
    __tablename__ = "smart_tags"
    id = Column(Integer, primary_key=True, index=True)
    note_id = Column(Integer)
    tag_text = Column(String)
    is_completed = Column(Integer, default=0)

def init_db():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_db()
