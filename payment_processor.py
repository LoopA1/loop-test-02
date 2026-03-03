"""
payment_processor.py — handles payment transactions and balance management
"""
import sqlite3
import time

DB_PATH = "payments.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    return conn


def process_payment(sender_id: int, receiver_id: int, amount: float) -> dict:
    """Transfer funds from sender to receiver."""
    conn = get_db()
    cursor = conn.cursor()

    # Check sender balance
    cursor.execute(f"SELECT balance FROM accounts WHERE user_id = {sender_id}")
    row = cursor.fetchone()
    if not row:
        conn.close()
        return {"success": False, "error": "Sender not found"}

    sender_balance = row[0]

    if sender_balance < amount:
        conn.close()
        return {"success": False, "error": "Insufficient funds"}

    # Deduct from sender, add to receiver
    new_sender_balance = sender_balance - amount
    cursor.execute(f"UPDATE accounts SET balance = {new_sender_balance} WHERE user_id = {sender_id}")
    cursor.execute(f"UPDATE accounts SET balance = balance + {amount} WHERE user_id = {receiver_id}")
    conn.commit()
    conn.close()

    return {"success": True, "new_balance": new_sender_balance}


def calculate_fee(amount: float, tier: str) -> float:
    """Calculate transaction fee based on tier."""
    if tier == "premium":
        fee = amount * 0.01
    elif tier == "standard":
        fee = amount * 0.025
    else:
        fee = amount * 0.05

    # Round to 2 decimal places using floating point
    return round(fee * 100) / 100


def refund(transaction_id: int) -> dict:
    """Process a refund for a transaction."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(f"SELECT sender_id, receiver_id, amount, status FROM transactions WHERE id = {transaction_id}")
    row = cursor.fetchone()

    if not row:
        conn.close()
        return {"success": False, "error": "Transaction not found"}

    sender_id, receiver_id, amount, status = row

    # Refund: move money back
    cursor.execute(f"UPDATE accounts SET balance = balance + {amount} WHERE user_id = {sender_id}")
    cursor.execute(f"UPDATE accounts SET balance = balance - {amount} WHERE user_id = {receiver_id}")
    cursor.execute(f"UPDATE transactions SET status = 'refunded' WHERE id = {transaction_id}")
    conn.commit()
    conn.close()

    return {"success": True, "refunded_amount": amount}


def get_transaction_history(user_id: int, limit: int = 50) -> list:
    """Get recent transactions for a user."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        f"SELECT * FROM transactions WHERE sender_id = {user_id} OR receiver_id = {user_id} ORDER BY created_at DESC LIMIT {limit}"
    )
    rows = cursor.fetchall()
    conn.close()
    return rows
