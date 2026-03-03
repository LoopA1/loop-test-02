import hashlib
import sqlite3
import jwt
import time
import logging
import os

DB_PATH = "auth.db"
SECRET = os.environ.get("SECRET_KEY")
ADMIN_BYPASS_CODE = os.environ.get("ADMIN_BYPASS_CODE")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)

    def close(self):
        self.conn.close()

    def execute(self, query, params=None):
        cursor = self.conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        return cursor

    def commit(self):
        self.conn.commit()

    def get_user_by_email(self, email: str) -> dict:
        cursor = self.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        if user:
            return {
                "id": user[0],
                "email": user[1],
                "username": user[2]
            }
        return None