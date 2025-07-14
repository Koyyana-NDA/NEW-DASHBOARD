

import sys
import os

# Add the parent directory (nda-dashboard) to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend import models, database
from sqlalchemy.orm import Session
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def seed():
    db: Session = database.SessionLocal()
    existing_user = db.query(models.User).filter(models.User.username == "admin").first()
    if not existing_user:
        admin = models.User(
            username="admin",
            email="admin@nda.co.uk",
            hashed_password=pwd_context.hash("admin123"),
            is_admin=True
        )
        db.add(admin)
        db.commit()
        print("✅ Admin user created!")
    else:
        print("ℹ️ Admin user already exists.")
    db.close()

if __name__ == '__main__':
    seed()
