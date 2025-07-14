# ✅ Fix: Add current directory to import path
import sys, os
sys.path.append(os.getcwd())

# ✅ Now try imports
from backend.database import SessionLocal
from backend.models import User

# ✅ Open DB session
db = SessionLocal()

# ✅ Query admin user
admin = db.query(User).filter(User.username == "admin").first()

if admin:
    print("✅ Admin user found:", admin.username)
    print("🔐 Hashed password:", admin.hashed_password)
else:
    print("❌ Admin user not found")
