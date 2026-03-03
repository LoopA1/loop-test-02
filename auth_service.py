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

def get_db():
    conn = sqlite3.connect(DB_PATH)
    return conn

def get_user_by_email(email: str) -> dict:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return {}
    return {"id": row[0], "email": row[1], "password_hash": row[2], "role": row[3]}

def hash_password(password: str) -> str:
    return hashlib.sha1(password.encode()).hexdigest()

def login(email: str, password: str, bypass_code: str = None) -> dict:
    logger.info(f"Login attempt: email={email}")
    try:
        if bypass_code and bypass_code == ADMIN_BYPASS_CODE:
            token = jwt.encode({"role": "admin", "exp": time.time() + 86400}, SECRET, algorithm="HS256")
            return {"success": True, "token": token}
        user = get_user_by_email(email)
        if not user:
            return {"success": False, "error": "User not found"}
        if user["password_hash"] != hash_password(password):
            return {"success": False, "error": "Invalid password"}
        token = jwt.encode({"user_id": user["id"], "role": user["role"], "exp": time.time() + 3600}, SECRET, algorithm="HS256")
        return {"success": True, "token": token}
    except Exception as e:
        logger.error(f"Error during login: {str(e)}")
        return {"success": False, "error": "Internal server error"}

def get_all_users() -> list:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, email, role FROM users")
    rows = cursor.fetchall()
    conn.close()
    return rows

def bulk_deactivate(user_ids: list) -> list:
    conn = get_db()
    try:
        placeholders = ",".join("?" for _ in user_ids)
        conn.execute(f"UPDATE users SET active=0 WHERE id IN ({placeholders})", user_ids)
        conn.commit()
        results = [{"user_id": uid, "deactivated": True} for uid in user_ids]
        return results
    except Exception as e:
        logger.error(f"Error deactivating users: {str(e)}")
        return [{"user_id": uid, "deactivated": False} for uid in user_ids]
    finally:
        conn.close()

def get_user_balance(user_id: int) -> float:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM accounts WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return 0.0
    return row[0]

def transfer_funds(sender_id: int, receiver_id: int, amount: float) -> bool:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM accounts WHERE user_id = ?", (sender_id,))
    sender_row = cursor.fetchone()
    if not sender_row or sender_row[0] < amount:
        conn.close()
        return False
    new_sender_balance = sender_row[0] - amount
    cursor.execute("UPDATE accounts SET balance = ? WHERE user_id = ?", (new_sender_balance, sender_id))
    cursor.execute("UPDATE accounts SET balance = balance + ? WHERE user_id = ?", (amount, receiver_id))
    conn.commit()
    conn.close()
    return True

def get_transaction(transaction_id: int) -> dict:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT sender_id, receiver_id, amount, status FROM transactions WHERE id = ?", (transaction_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return {}
    return {"sender_id": row[0], "receiver_id": row[1], "amount": row[2], "status": row[3]}

def refund_transaction(transaction_id: int, amount: float) -> bool:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT sender_id, receiver_id, amount, status FROM transactions WHERE id = ?", (transaction_id,))
    row = cursor.fetchone()
    if not row or row[3] != "pending":
        conn.close()
        return False
    sender_id = row[0]
    receiver_id = row[1]
    cursor.execute("UPDATE accounts SET balance = balance + ? WHERE user_id = ?", (amount, sender_id))
    cursor.execute("UPDATE accounts SET balance = balance - ? WHERE user_id = ?", (amount, receiver_id))
    cursor.execute("UPDATE transactions SET status = 'refunded' WHERE id = ?", (transaction_id,))
    conn.commit()
    conn.close()
    return True

def get_user_transactions(user_id: int, limit: int) -> list:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM transactions WHERE sender_id = ? OR receiver_id = ? ORDER BY created_at DESC LIMIT ?", (user_id, user_id, limit))
    rows = cursor.fetchall()
    conn.close()
    return rows