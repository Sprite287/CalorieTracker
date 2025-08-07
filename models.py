from database import db
from datetime import datetime

class Profile(db.Model):
    __tablename__ = 'profiles'
    profile_name = db.Column(db.String, primary_key=True)
    data = db.Column(db.Text)  # JSON string for food_database and settings only
    uuid = db.Column(db.String, unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to weekly logs
    weekly_logs = db.relationship("WeeklyLog", back_populates="profile", cascade="all, delete-orphan")

class WeeklyLog(db.Model):
    __tablename__ = 'weekly_log'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    profile_name = db.Column(db.String, db.ForeignKey('profiles.profile_name'), nullable=False)
    date = db.Column(db.String, nullable=False, index=True)  # Store as YYYY-MM-DD string with index
    meal_type = db.Column(db.String, nullable=False)
    food_id = db.Column(db.String, unique=True, nullable=False)
    food_name = db.Column(db.String, nullable=False)
    calories = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, default=1, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship back to profile
    profile = db.relationship("Profile", back_populates="weekly_logs")
    
    # Add composite index for common queries
    __table_args__ = (
        db.Index('idx_profile_date', 'profile_name', 'date'),
    )
