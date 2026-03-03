import sqlite3
import jwt
import time
import logging
import os
import hashlib
import secrets
import string
from data_cache import CacheManager, cache_key_from_query

DB_PATH = 'auth.db'
SECRET = os.environ.get('SECRET_KEY')
ADMIN_BYPASS_CODE = os.environ.get('ADMIN_BYPASS_CODE')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()
        self.cache = CacheManager()

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

    def get_users(self) -> list:
        self.cursor.execute('SELECT * FROM users')
        users = self.cursor.fetchall()
        return users

    def get_user_by_email(self, email: str) -> dict:
        cache_key = cache_key_from_query('SELECT * FROM users WHERE email = ?', {'email': email})
        user = self.cache.get_or_fetch(cache_key, lambda: self._get_user_by_email(email))
        return user

    def _get_user_by_email(self, email: str) -> dict:
        query = 'SELECT * FROM users WHERE email = ?'
        params = (email,)
        self.cursor.execute(query, params)
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
        query = 'INSERT INTO users (email, username, password) VALUES (?, ?, ?)'
        params = (email, username, hashed_password)
        self.cursor.execute(query, params)
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