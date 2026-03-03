import sqlite3
import time

DB_PATH = "payments.db"

class PaymentProcessor:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()
        self.batch_size = 100

    def _get_sender_balance(self, sender_id: int) -> float:
        self.cursor.execute("SELECT balance FROM accounts WHERE user_id = ?", (sender_id,))
        row = self.cursor.fetchone()
        if not row:
            return None
        return row[0]

    def _update_balance(self, user_id: int, amount: float) -> None:
        self.cursor.execute("UPDATE accounts SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
        self.conn.commit()

    def _check_sender_balance(self, sender_id: int, amount: float) -> bool:
        sender_balance = self._get_sender_balance(sender_id)
        if sender_balance is None:
            return False
        return sender_balance >= amount

    def _perform_transaction(self, sender_id: int, receiver_id: int, amount: float) -> None:
        self._update_balance(sender_id, -amount)
        self._update_balance(receiver_id, amount)

    def _validate_payment(self, sender_id: int, receiver_id: int, amount: float) -> bool:
        return self._check_sender_balance(sender_id, amount)

    def _log_payment(self, sender_id: int, receiver_id: int, amount: float) -> None:
        self.cursor.execute("INSERT INTO transactions (sender_id, receiver_id, amount) VALUES (?, ?, ?)", (sender_id, receiver_id, amount))
        self.conn.commit()

    def process_payment(self, sender_id: int, receiver_id: int, amount: float) -> dict:
        if not self._validate_payment(sender_id, receiver_id, amount):
            return {"success": False, "error": "Insufficient funds"}
        self._perform_transaction(sender_id, receiver_id, amount)
        self._log_payment(sender_id, receiver_id, amount)
        return {"success": True, "new_balance": self._get_sender_balance(sender_id)}

    def calculate_fee(self, amount: float, tier: str) -> float:
        if tier == "premium":
            fee = amount * 0.01
        elif tier == "standard":
            fee = amount * 0.025
        else:
            fee = amount * 0.05
        return round(fee * 100) / 100

    def refund(self, transaction_id: int) -> dict:
        self.cursor.execute("SELECT sender_id, receiver_id, amount, status FROM transactions WHERE id = ?", (transaction_id,))
        row = self.cursor.fetchone()
        if not row:
            return {"success": False, "error": "Transaction not found"}
        sender_id, receiver_id, amount, status = row
        self._update_balance(sender_id, amount)
        self._update_balance(receiver_id, -amount)
        self.cursor.execute("UPDATE transactions SET status = ? WHERE id = ?", ("refunded", transaction_id))
        self.conn.commit()
        return {"success": True, "refunded_amount": amount}

    def get_transaction_history(self, user_id: int, limit: int = 50) -> list:
        self.cursor.execute("SELECT * FROM transactions WHERE sender_id = ? OR receiver_id = ? ORDER BY created_at DESC LIMIT ?", (user_id, user_id, limit))
        rows = self.cursor.fetchall()
        return rows

    def get_all_users(self) -> list:
        users = []
        offset = 0
        while True:
            self.cursor.execute("SELECT user_id FROM accounts LIMIT ? OFFSET ?", (self.batch_size, offset))
            rows = self.cursor.fetchall()
            if not rows:
                break
            users.extend([row[0] for row in rows])
            offset += self.batch_size
        return users

    def get_transaction_history_for_users(self, user_ids: list, limit: int = 50) -> list:
        query = "SELECT * FROM transactions WHERE sender_id IN (" + ",".join(["?" for _ in user_ids]) + ") OR receiver_id IN (" + ",".join(["?" for _ in user_ids]) + ") ORDER BY created_at DESC LIMIT ?"
        self.cursor.execute(query, (*user_ids, *user_ids, limit))
        rows = self.cursor.fetchall()
        return rows

    def close_connection(self):
        self.conn.close()

if __name__ == "__main__":
    processor = PaymentProcessor()
    processor.close_connection()