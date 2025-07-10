from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float, Date, Text

Base = declarative_base()

class Profile(Base):
    __tablename__ = 'profiles'
    profile_name = Column(String, primary_key=True)
    data = Column(Text)  # JSON string, now using Text for scalability

class WeeklyLog(Base):
    __tablename__ = 'weekly_log'
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(String)  # Store as YYYY-MM-DD string
    meal_type = Column(String)
    food_id = Column(String)
    food_name = Column(String)
    calories = Column(Integer)
    quantity = Column(Integer, default=1)
