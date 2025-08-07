from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Text, Index, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Profile(Base):
    __tablename__ = 'profiles'
    profile_name = Column(String, primary_key=True)
    data = Column(Text)  # JSON string for food_database and settings only
    uuid = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship to weekly logs
    weekly_logs = relationship("WeeklyLog", back_populates="profile", cascade="all, delete-orphan")

class WeeklyLog(Base):
    __tablename__ = 'weekly_log'
    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_name = Column(String, ForeignKey('profiles.profile_name'), nullable=False)
    date = Column(String, nullable=False, index=True)  # Store as YYYY-MM-DD string with index
    meal_type = Column(String, nullable=False)
    food_id = Column(String, unique=True, nullable=False)
    food_name = Column(String, nullable=False)
    calories = Column(Integer, nullable=False)
    quantity = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship back to profile
    profile = relationship("Profile", back_populates="weekly_logs")
    
    # Add composite index for common queries
    __table_args__ = (
        Index('idx_profile_date', 'profile_name', 'date'),
    )
