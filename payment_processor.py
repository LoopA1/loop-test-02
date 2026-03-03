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

class TransactionPerformer:
    def __init__(self, conn):
        self.conn = conn
        self.cursor = self.conn.cursor()

    def perform_transaction(self, sender_id: int, receiver_id: int, amount: float) -> None:
        self.cursor.execute("UPDATE accounts SET balance = balance - ? WHERE user_id = ?", (amount, sender_id))
        self.cursor.execute("UPDATE accounts SET balance = balance + ? WHERE user_id = ?", (amount, receiver_id))
        self.conn.commit()

    def log_payment(self, sender_id: int, receiver_id: int, amount: float) -> None:
        self.cursor.execute("INSERT INTO transactions (sender_id, receiver_id, amount) VALUES (?, ?, ?)", (sender_id, receiver_id, amount))
        self.conn.commit()

class PaymentProcessor:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.balance_checker = BalanceChecker(self.conn)
        self.transaction_performer = TransactionPerformer(self.conn)
        self.batch_size = 100

    def process_payment(self, sender_id: int, receiver_id: int, amount: float) -> dict:
        if not self.balance_checker.check_sender_balance(sender_id, amount):
            return {"success": False, "error": "Insufficient funds"}
        self.transaction_performer.perform_transaction(sender_id, receiver_id, amount)
        self.transaction_performer.log_payment(sender_id, receiver_id, amount)
        return {"success": True, "new_balance": self.balance_checker.get_sender_balance(sender_id)}

    def calculate_fee(self, amount: float, tier: str) -> float:
        if tier == "premium":
            fee = amount * 0.01
        elif tier == "standard":
            fee = amount * 0.025
        else:
            fee = amount * 0.05
        return round(fee * 100) / 100

    def refund(self, transaction_id: int) -> dict:
        self.cursor = self.conn.cursor()
        self.cursor.execute("SELECT sender_id, receiver_id, amount, status FROM transactions WHERE id = ?", (transaction_id,))
        row = self.cursor.fetchone()
        if not row:
            return {"success": False, "error": "Transaction not found"}
        sender_id, receiver_id, amount, status = row
        self.balance_checker.update_balance(sender_id, amount)
        self.balance_checker.update_balance(receiver_id, -amount)
        self.cursor.execute("UPDATE transactions SET status = ? WHERE id = ?", ("refunded", transaction_id))
        self.conn.commit()
        return {"success": True, "refunded_amount": amount}

    def get_transaction_history(self, user_id: int, limit: int = 50) -> list:
        self.cursor = self.conn.cursor()
        self.cursor.execute("SELECT * FROM transactions WHERE sender_id = ? OR receiver_id = ? ORDER BY created_at DESC LIMIT ?", (user_id, user_id, limit))
        rows = self.cursor.fetchall()
        return rows

    def get_all_users(self) -> list:
        users = []
        self.cursor = self.conn.cursor()
        self.cursor.execute("SELECT user_id FROM accounts")
        rows = self.cursor.fetchall()
        users = [row[0] for row in rows]
        return users

    def get_transaction_history_for_users(self, user_ids: list, limit: int = 50) -> list:
        query = "SELECT * FROM transactions WHERE sender_id IN (" + ",".join(["?" for _ in user_ids]) + ") OR receiver_id IN (" + ",".join(["?" for _ in user_ids]) + ") ORDER BY created_at DESC LIMIT ?"
        self.cursor = self.conn.cursor()
        self.cursor.execute(query, (*user_ids, *user_ids, limit))
        rows = self.cursor.fetchall()
        return rows

    def close_connection(self):
        self.conn.close()

if __name__ == "__main__":
    processor = PaymentProcessor()
    processor.close_connection()