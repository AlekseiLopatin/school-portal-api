"""
JWT authentication — password hashing, token issuance, and the dependency
that protects write routes.

Flow:
    1. POST /auth/login with username + password (OAuth2 password form)
    2. We verify the password against the bcrypt hash stored on the User row
    3. We issue a short-lived JWT signed with SECRET_KEY
    4. Protected routes depend on get_current_user, which decodes the token
       from the Authorization: Bearer <token> header and loads the user

There is no public registration endpoint. The one admin account is created
via seed_admin.py, reading credentials from environment variables.
"""
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

import models
from database import get_db

# SECRET_KEY must be set in production (Railway env var). The fallback here
# is only for local dev convenience — never rely on it outside your own machine.
SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-insecure-secret-do-not-use-in-prod")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def get_user(db: Session, username: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.username == username).first()


def authenticate_user(
    db: Session, username: str, password: str
) -> Optional[models.User]:
    user = get_user(db, username)
    if user is None or not verify_password(password, user.hashed_password):
        return None
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> models.User:
    """
    Dependency for protected routes. Decodes the bearer token, looks up the
    user, and raises 401 on any failure (missing/invalid/expired token,
    or a token for a user that no longer exists).
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: Optional[str] = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = get_user(db, username)
    if user is None:
        raise credentials_exception
    return user
