import sqlite3
import jwt
import time
import logging
import os
import hashlib
import secrets
import string
from data_cache import cache_get, cache_set
from passlib.context import CryptContext
from user_validator import UserValidator
import re

DB_PATH = 'auth.db'
SECRET = os.environ.get('SECRET_KEY')
ADMIN_BYPASS_CODE = os.environ.get('ADMIN_BYPASS_CODE')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=['bcrypt'], default='bcrypt')

class AuthService:
    def __init__(self):
        self.validator = UserValidator()

    def validate_registration(self, data: dict) -> dict:
        return self.validator.validate_registration(data)

    def validate_role(self, role: str) -> dict:
        return self.validator.validate_role(role)