# Script to force table creation on Render
from db_orm import engine
from models import Base

if __name__ == "__main__":
    print("Creating all tables...")
    Base.metadata.create_all(engine)
    print("Done.")
