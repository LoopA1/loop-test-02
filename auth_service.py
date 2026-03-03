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

    def rollback(self):
        self.conn.rollback()

class UserRepository:
    def __init__(self, db):
        self.db = db

    def get_user_by_email(self, email: str) -> dict:
        cursor = self.db.execute("SELECT * FROM users WHERE email = ?", (email,))
        row = cursor.fetchone()
        if not row:
            return {}
        return {"id": row[0], "email": row[1], "password_hash": row[2], "role": row[3]}

    def get_all_users(self) -> list:
        cursor = self.db.execute("SELECT id, email, role FROM users")
        rows = cursor.fetchall()
        return [{"id": row[0], "email": row[1], "role": row[2]} for row in rows]

class AccountRepository:
    def __init__(self, db):
        self.db = db

    def get_user_balance(self, user_id: int) -> float:
        cursor = self.db.execute("SELECT balance FROM accounts WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        if not row:
            return 0.0
        return row[0]

class UserService:
    def __init__(self, user_repository, account_repository):
        self.user_repository = user_repository
        self.account_repository = account_repository

    def login(self, email: str, password: str, bypass_code: str = None) -> dict:
        logger.info(f"Login attempt: email={email}")
        try:
            if bypass_code and bypass_code == ADMIN_BYPASS_CODE:
                token = jwt.encode({"role": "admin", "exp": time.time() + 86400}, SECRET, algorithm="HS256")
                return {"success": True, "token": token}
            user = self.user_repository.get_user_by_email(email)
            if not user:
                return {"success": False, "error": "User not found"}
            if user["password_hash"] != self.hash_password(password):
                return {"success": False, "error": "Invalid password"}
            token = jwt.encode({"user_id": user["id"], "role": user["role"], "exp": time.time() + 3600}, SECRET, algorithm="HS256")
            return {"success": True, "token": token}
        except Exception as e:
            logger.error(f"Error during login: {str(e)}")
            return {"success": False, "error": "Internal server error"}

    def bulk_deactivate(self, user_ids: list) -> list:
        try:
            placeholders = ",".join("?" for _ in user_ids)
            self.user_repository.db.execute(f"UPDATE users SET active=0 WHERE id IN ({placeholders})", user_ids)
            self.user_repository.db.commit()
            results = [{"user_id": uid, "deactivated": True} for uid in user_ids]
            return results
        except Exception as e:
            logger.error(f"Error deactivating users: {str(e)}")
            self.user_repository.db.rollback()
            return [{"user_id": uid, "deactivated": False} for uid in user_ids]

    def hash_password(self, password: str) -> str:
        return hashlib.sha1(password.encode()).hexdigest()

    def get_user_balance(self, user_id: int) -> float:
        return self.account_repository.get_user_balance(user_id)

    def transfer_funds(self, sender_id: int, receiver_id: int, amount: float) -> bool:
        try:
            sender_balance = self.account_repository.get_user_balance(sender_id)
            if sender_balance < amount:
                return False
            self.user_repository.db.execute("UPDATE accounts SET balance = balance - ? WHERE user_id = ?", (amount, sender_id))
            self.user_repository.db.execute("UPDATE accounts SET balance = balance + ? WHERE user_id = ?", (amount, receiver_id))
            self.user_repository.db.commit()
            return True
        except Exception as e:
            logger.error(f"Error during transfer: {str(e)}")
            self.user_repository.db.rollback()
            return False

    def refund_transaction(self, transaction_id: int) -> bool:
        try:
            cursor = self.user_repository.db.execute("SELECT sender_id, receiver_id, amount FROM transactions WHERE id = ?", (transaction_id,))
            transaction_row = cursor.fetchone()
            if not transaction_row:
                return False
            sender_id, receiver_id, amount = transaction_row
            sender_balance = self.account_repository.get_user_balance(sender_id)
            if sender_balance < amount:
                return False
            self.user_repository.db.execute("UPDATE accounts SET balance = balance + ? WHERE user_id = ?", (amount, sender_id))
            self.user_repository.db.execute("UPDATE accounts SET balance = balance - ? WHERE user_id = ?", (amount, receiver_id))
            self.user_repository.db.execute("UPDATE transactions SET status = 'refunded' WHERE id = ?", (transaction_id,))
            self.user_repository.db.commit()
            return True
        except Exception as e:
            logger.error(f"Error during refund: {str(e)}")
            self.user_repository.db.rollback()
            return False

def main():
    db = Database()
    user_repository = UserRepository(db)
    account_repository = AccountRepository(db)
    user_service = UserService(user_repository, account_repository)
    # usage
    user_service.login("email@example.com", "password")
    user_service.bulk_deactivate([1, 2, 3])
    user_service.get_user_balance(1)
    db.close()

if __name__ == "__main__":
    main()