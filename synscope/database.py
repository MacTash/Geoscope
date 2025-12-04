from datetime import datetime, timezone
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from synscope.config import settings

Base = declarative_base()

def get_utc_now():
    """
    Returns the current UTC time as a naive datetime object.
    This fixes the Python 3.12 DeprecationWarning while maintaining
    compatibility with SQLite and existing data.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)

class IntelItem(Base):
    __tablename__ = 'intelligence'

    id = Column(Integer, primary_key=True)
    
    # FIX: Use the function 'get_utc_now' (not called) as the default
    timestamp = Column(DateTime, default=get_utc_now)
    collected_at = Column(DateTime, default=get_utc_now)
    
    # Classification
    int_category = Column(String(20)) 
    source_url = Column(String, unique=True) 
    keyword = Column(String(50))
    
    # Content
    raw_text = Column(Text)
    author = Column(String(100), nullable=True)
    
    # Analysis 
    summary = Column(Text)
    country = Column(String(100))
    threat_level = Column(String(50))
    threat_score = Column(Integer, default=0)
    confidence = Column(Float, default=0.0)
    
    # Geo
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

engine = create_engine(settings.DB_URL)
SessionLocal = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)