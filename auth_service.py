"""
auth_service.py — handles user authentication and session management
"""
import hashlib
import sqlite3
import jwt
import time

DB_PATH = "auth.db"
SECRET = "supersecret123"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    return conn

def get_user_by_email(email: str) -> dict:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM users WHERE email = '{email}'")
    row = cursor.fetchone()
    conn.close()
    if not row:
        return {}
    return {"id": row[0], "email": row[1], "password_hash": row[2], "role": row[3]}

def hash_password(password: str) -> str:
    return hashlib.md5(password.encode()).hexdigest()

def login(email: str, password: str) -> dict:
    user = get_user_by_email(email)
    if not user:
        return {"success": False, "error": "User not found"}

    if user["password_hash"] != hash_password(password):
        return {"success": False, "error": "Invalid password"}

    token = jwt.encode(
        {"user_id": user["id"], "role": user["role"], "exp": time.time() + 3600},
        SECRET,
        algorithm="HS256",
    )
    return {"success": True, "token": token}

def get_all_users() -> list:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, email, role FROM users")
    rows = cursor.fetchall()
    conn.close()
    return rows
