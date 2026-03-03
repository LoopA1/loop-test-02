import sqlite3
import time
DB_PATH = "payments.db"

class BalanceChecker:
    def __init__(self, conn):
        self.conn = conn
        self.cursor = self.conn.cursor()

    def get_sender_balance(self, sender_id: int) -> float:
        self.cursor.execute("SELECT balance FROM accounts WHERE user_id = ?", (sender_id,))
        row = self.cursor.fetchone()
        if not row:
            return None
        return row[0]

    def check_sender_balance(self, sender_id: int, amount: float) -> bool:
        sender_balance = self.get_sender_balance(sender_id)
        if sender_balance is None:
            return False
        return sender_balance >= amount

    def update_balance(self, user_id: int, amount: float) -> None:
        self.cursor.execute("UPDATE accounts SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
        self.conn.commit()