import sqlite3
import jwt
import time
import logging
import os
import hashlib
import secrets
import string

DB_PATH = 'auth.db'
SECRET = os.environ.get('SECRET_KEY')
ADMIN_BYPASS_CODE = os.environ.get('ADMIN_BYPASS_CODE')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()

    def close(self):
        self.conn.close()

    def execute(self, query, params=None):
        if params:
            self.cursor.execute(query, params)
        else:
            self.cursor.execute(query)
        return self.cursor

    def commit(self):
        self.conn.commit()

    def get_user_by_email(self, email: str) -> dict:
        self.cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = self.cursor.fetchone()
        if user:
            return {
                'id': user[0],
                'email': user[1],
                'username': user[2],
                'password': user[3]
            }
        return None

    def create_user(self, email: str, username: str, password: str) -> dict:
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        self.cursor.execute('INSERT INTO users (email, username, password) VALUES (?, ?, ?)', (email, username, hashed_password))
        self.commit()
        return self.get_user_by_email(email)

    def authenticate_user(self, email: str, password: str) -> dict:
        user = self.get_user_by_email(email)
        if user:
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            if user['password'] == hashed_password:
                return user
        return None

    def validate_user_data(self, email: str, username: str, password: str) -> dict:
        errors = {}
        if not email:
            errors['email'] = 'Email is required'
        if not username:
            errors['username'] = 'Username is required'
        if not password:
            errors['password'] = 'Password is required'
        return errors

    def register_user(self, email: str, username: str, password: str) -> dict:
        errors = self.validate_user_data(email, username, password)
        if errors:
            return {'success': False, 'errors': errors}
        return self.create_user(email, username, password)

    def login_user(self, email: str, password: str) -> dict:
        errors = {}
        if not email:
            errors['email'] = 'Email is required'
        if not password:
            errors['password'] = 'Password is required'
        if errors:
            return {'success': False, 'errors': errors}
        return self.authenticate_user(email, password)

    def validate_and_create_user(self, email: str, username: str, password: str) -> dict:
        errors = self.validate_user_data(email, username, password)
        if errors:
            return {'success': False, 'errors': errors}
        return self.create_user(email, username, password)

    def validate_and_authenticate_user(self, email: str, password: str) -> dict:
        errors = {}
        if not email:
            errors['email'] = 'Email is required'
        if not password:
            errors['password'] = 'Password is required'
        if errors:
            return {'success': False, 'errors': errors}
        return self.authenticate_user(email, password)