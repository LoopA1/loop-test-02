import sqlite3
import jwt
import time
import logging
import os
import hashlib
import secrets
import string
from data_cache import CacheManager, cache_key_from_query
from passlib.context import CryptContext
from user_validator import UserValidator

DB_PATH = 'auth.db'
SECRET = os.environ.get('SECRET_KEY')
ADMIN_BYPASS_CODE = os.environ.get('ADMIN_BYPASS_CODE')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=['bcrypt'], default='bcrypt')

class UserValidator:
    def validate_registration(self, data: dict) -> dict:
        results = {}
        results['username'] = self.validate_username(data.get('username', ''))
        results['email'] = self.validate_email(data.get('email', ''))
        results['password'] = self.validate_password(data.get('password', ''))
        if 'role' in data:
            results['role'] = self.validate_role(data['role'])
        all_valid = all(r['valid'] for r in results.values())
        return {'valid': all_valid, 'fields': results}

    def validate_username(self, username: str) -> dict:
        errors = []
        if not username or len(username.strip()) == 0:
            errors.append('Username is required')
        if len(username) < 2:
            errors.append('Username must be at least 2 characters')
        if len(username) > 50:
            errors.append('Username must be at most 50 characters')
        if not re.match(r'^[a-zA-Z0-9._-]+$', username):
            errors.append('Username can only contain letters, numbers, dots, underscores, and hyphens')
        return {'valid': len(errors) == 0, 'errors': errors}

    def validate_email(self, email: str) -> dict:
        errors = []
        if not email or len(email.strip()) == 0:
            errors.append('Email is required')
        pattern = r'^([a-zA-Z0-9_.+-]+)@([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            errors.append('Invalid email format')
        return {'valid': len(errors) == 0, 'errors': errors}

    def validate_password(self, password: str) -> dict:
        errors = []
        if not password or len(password.strip()) == 0:
            errors.append('Password is required')
        if len(password) < 8:
            errors.append('Password must be at least 8 characters')
        return {'valid': len(errors) == 0, 'errors': errors}