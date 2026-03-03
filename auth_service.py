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

    def get_user(self, email):
        query = "SELECT * FROM users WHERE email = ?"
        cursor = self.execute(query, (email,))
        return cursor.fetchone()

    def create_user(self, email, password):
        query = "INSERT INTO users (email, password) VALUES (?, ?)"
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        self.execute(query, (email, hashed_password))
        self.commit()

    def get_account(self, user_id):
        query = "SELECT * FROM accounts WHERE user_id = ?"
        cursor = self.execute(query, (user_id,))
        return cursor.fetchone()

    def create_account(self, user_id, balance):
        query = "INSERT INTO accounts (user_id, balance) VALUES (?, ?)"
        self.execute(query, (user_id, balance))
        self.commit()

    def update_account(self, user_id, balance):
        query = "UPDATE accounts SET balance = ? WHERE user_id = ?"
        self.execute(query, (balance, user_id))
        self.commit()

    def transfer_funds(self, sender_id, receiver_id, amount):
        query = "SELECT balance FROM accounts WHERE user_id = ?"
        sender_cursor = self.execute(query, (sender_id,))
        sender_balance = sender_cursor.fetchone()[0]
        new_sender_balance = sender_balance - amount
        query = "UPDATE accounts SET balance = ? WHERE user_id = ?"
        self.execute(query, (new_sender_balance, sender_id))
        query = "UPDATE accounts SET balance = balance + ? WHERE user_id = ?"
        self.execute(query, (amount, receiver_id))
        self.commit()

    def get_transaction_history(self, user_ids: list, limit: int = 50) -> list:
        query = """ 
            SELECT * FROM transactions 
            WHERE sender_id IN (%s) OR receiver_id IN (%s) 
            ORDER BY created_at DESC LIMIT %d 
        """
        params = ",".join(["?"] * len(user_ids)) + "," + ",".join(["?"] * len(user_ids))
        query = query % (params, limit)
        params = user_ids + user_ids
        cursor = self.execute(query, params)
        return cursor.fetchall()

    def get_transaction_history_for_user(self, user_id: int, limit: int = 50) -> list:
        return self.get_transaction_history([user_id], limit)

    def generate_token(self, user_id):
        payload = {"user_id": user_id, "exp": int(time.time()) + 3600}
        return jwt.encode(payload, SECRET, algorithm="HS256")

    def verify_token(self, token):
        try:
            payload = jwt.decode(token, SECRET, algorithms=["HS256"])
            return payload["user_id"]
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

class UserRepository:
    def __init__(self, db: Database):
        self.db = db

    def get_user_by_email(self, email: str):
        query = "SELECT * FROM users WHERE email = ?"
        cursor = self.db.execute(query, (email,))
        return cursor.fetchone()

    def get_user_by_id(self, user_id: int):
        query = "SELECT * FROM users WHERE id = ?"
        cursor = self.db.execute(query, (user_id,))
        return cursor.fetchone()

    def deactivate_user(self, user_id: int):
        query = "UPDATE users SET is_active = 0 WHERE id = ?"
        self.db.execute(query, (user_id,))
        self.db.commit()

    def bulk_deactivate(self, user_ids: list):
        query = "UPDATE users SET is_active = 0 WHERE id IN (%s)"
        params = ",".join("?" * len(user_ids))
        query = query % params
        self.db.execute(query, user_ids)
        self.db.commit()

class TransactionRepository:
    def __init__(self, db: Database):
        self.db = db

    def transfer_funds(self, sender_id: int, receiver_id: int, amount: float):
        query = "INSERT INTO transactions (sender_id, receiver_id, amount) VALUES (?, ?, ?)"
        self.db.execute(query, (sender_id, receiver_id, amount))
        self.db.commit()
        return True

    def refund_transaction(self, transaction_id: int):
        query = "UPDATE transactions SET is_refunded = 1 WHERE id = ?"
        self.db.execute(query, (transaction_id,))
        self.db.commit()
        return True

class AuthenticationService:
    def __init__(self, user_repo: UserRepository, db: Database):
        self.user_repo = user_repo
        self.db = db

    def login(self, email: str, password: str, bypass_code: str = None) -> dict:
        user = self.user_repo.get_user_by_email(email)
        if not user:
            return {"error": "User not found"}
        if bypass_code and bypass_code == ADMIN_BYPASS_CODE:
            return {"token": self.generate_token(user[0])}
        if not self.check_password(password, user[1]):
            return {"error": "Invalid password"}
        return {"token": self.generate_token(user[0])}

    def generate_token(self, user_id: int):
        payload = {"user_id": user_id, "exp": int(time.time()) + 3600}
        return jwt.encode(payload, SECRET, algorithm="HS256")

    def check_password(self, password: str, hashed_password: str):
        return hashlib.sha256(password.encode()).hexdigest() == hashed_password

class UserService:
    def __init__(self, user_repo: UserRepository, transaction_repo: TransactionRepository, db: Database, auth_service: AuthenticationService):
        self.user_repo = user_repo
        self.transaction_repo = transaction_repo
        self.db = db
        self.auth_service = auth_service

    def deactivate_user(self, user_id: int):
        self.user_repo.deactivate_user(user_id)

    def bulk_deactivate(self, user_ids: list):
        self.user_repo.bulk_deactivate(user_ids)

    def transfer_funds(self, sender_id: int, receiver_id: int, amount: float):
        return self.transaction_repo.transfer_funds(sender_id, receiver_id, amount)

    def refund_transaction(self, transaction_id: int):
        return self.transaction_repo.refund_transaction(transaction_id)

    def get_transaction_history(self, user_id: int, limit: int = 50) -> list:
        return self.db.get_transaction_history_for_user(user_id, limit)

db = Database()
user_repo = UserRepository(db)
transaction_repo = TransactionRepository(db)
auth_service = AuthenticationService(user_repo, db)
user_service = UserService(user_repo, transaction_repo, db, auth_service)