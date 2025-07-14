# ✅ Corrected version of reset_db.py to fix import errors
# Run this file as a script from the root directory

import sys
import os

# Add backend directory to sys.path to fix imports
sys.path.append(os.path.join(os.path.dirname(__file__)))
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.database import Base, engine
from backend import models

# print("\U00002705 Loaded DATABASE_URL:", engine.url)

# WARNING: This will drop all tables and recreate them
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
exit()
# print("\U0001F4BE Database tables dropped and recreated successfully.")
