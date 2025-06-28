from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.database import get_async_session
from app.models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

import logging
from functools import wraps
import time
import ipaddress

from app.config import settings
from app.core.exceptions import SecurityException, ValidationException


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password) 