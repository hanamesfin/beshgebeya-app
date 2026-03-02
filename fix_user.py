from app import app, db, User
from sqlalchemy import text
import sys
with app.app_context():
    # Attempt to add is_denied column if it doesn't exist
    try:
        db.session.execute(text('ALTER TABLE user ADD COLUMN is_denied BOOLEAN DEFAULT 0'))
        db.session.commit()
        print("is_denied column added successfully")
    except Exception as e:
        db.session.rollback()
        print(f"Column might already exist or error occurred: {e}")
