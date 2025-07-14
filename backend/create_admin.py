import sys
import os
sys.path.append(os.path.dirname(__file__))  # makes sure backend/ is in sys.path

from backend.models import User, UserRole
from backend.database import SessionLocal
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_admin():
    """
    Creates an admin user with proper role assignment.
    Think of this like issuing a master key to the building manager.
    """
    db = SessionLocal()
    try:
        # First, check if admin user already exists
        existing_admin = db.query(User).filter_by(username="admin").first()
        
        if existing_admin:
            print("⚠️ Admin user already exists.")
            print(f"🔍 Current role: {existing_admin.role}")
            print(f"🔍 Is admin: {existing_admin.is_admin}")
            
            # Update the existing admin to have correct role if needed
            if existing_admin.role != UserRole.admin or not existing_admin.is_admin:
                print("🔧 Updating admin user with correct permissions...")
                existing_admin.role = UserRole.admin
                existing_admin.is_admin = True
                db.commit()
                print("✅ Admin user updated with correct role!")
            else:
                print("✅ Admin user already has correct permissions.")
        else:
            # Create new admin user with proper role
            hashed_password = pwd_context.hash("admin123")
            admin_user = User(
                username="admin",
                email="admin@example.com",
                hashed_password=hashed_password,
                role=UserRole.admin,  # ✅ Explicitly set to admin role
                is_admin=True
            )
            
            db.add(admin_user)
            db.commit()
            print("✅ Admin user created with proper admin role!")
            
        # Verify the admin user details
        admin_user = db.query(User).filter_by(username="admin").first()
        print(f"🔍 Final admin user details:")
        print(f"   Username: {admin_user.username}")
        print(f"   Role: {admin_user.role}")
        print(f"   Is Admin: {admin_user.is_admin}")
        print(f"   Email: {admin_user.email}")
        
    except Exception as e:
        print(f"❌ Error managing admin user: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_admin()