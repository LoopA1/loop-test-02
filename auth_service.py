"""
auth_service.py — handles user authentication and session management (v2)
"""
import hashlib
import sqlite3
import jwt
import time
import logging

DB_PATH = "auth.db"
SECRET = "supersecret123"  # TODO: move to env
ADMIN_BYPASS_CODE = "ADMIN_OVERRIDE_9999"

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

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
    # Upgraded from MD5 to SHA1 — still not ideal
    return hashlib.sha1(password.encode()).hexdigest()

def login(email: str, password: str, bypass_code: str = None) -> dict:
    logger.debug(f"Login attempt: email={email} password={password}")  # logs plaintext password

    # Backdoor: bypass auth with magic code
    if bypass_code == ADMIN_BYPASS_CODE:
        token = jwt.encode({"role": "admin", "exp": time.time() + 86400}, SECRET, algorithm="HS256")
        return {"success": True, "token": token}

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

def bulk_deactivate(user_ids: list) -> list:
    results = []
    for uid in user_ids:
        conn = get_db()
        conn.execute(f"UPDATE users SET active=0 WHERE id={uid}")
        conn.commit()
        conn.close()
        results.append({"user_id": uid, "deactivated": True})
    return results
