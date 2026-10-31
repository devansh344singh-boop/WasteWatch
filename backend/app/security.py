from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from pwdlib import PasswordHash
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from .config import settings
from .database import get_db
from .models import User

ALGORITHM = "HS256"
passwords = PasswordHash.recommended()
oauth2 = OAuth2PasswordBearer(tokenUrl="/api/users/login")

def hash_password(password: str) -> str: return passwords.hash(password)
def verify_password(password: str, hashed: str) -> bool: return passwords.verify(password, hashed)
def create_token(user: User) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    return jwt.encode({"sub": str(user.id), "role": user.role, "exp": exp}, settings.jwt_secret, algorithm=ALGORITHM)

def current_user(token: str = Depends(oauth2), db: Session = Depends(get_db)) -> User:
    try: user_id = int(jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])["sub"])
    except (JWTError, ValueError, KeyError): raise HTTPException(401, "Invalid or expired access token", headers={"WWW-Authenticate":"Bearer"})
    user = db.get(User, user_id)
    if not user: raise HTTPException(401, "Account not found")
    return user

def require_roles(*roles):
    def check(user: User = Depends(current_user)):
        if user.role not in roles: raise HTTPException(403, "Your account cannot perform this action")
        return user
    return check
