import os, datetime, jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.hash import bcrypt

SECRET_KEY = os.getenv("SECRET_KEY", "dev_secret_change_me")
ALGO = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "10080"))
_auth = HTTPBearer()

def hash_password(pw: str) -> str:
    return bcrypt.hash(pw)

def verify_password(pw: str, hashed: str) -> bool:
    return bcrypt.verify(pw, hashed)

def create_token(payload: dict) -> str:
    exp = datetime.datetime.utcnow() + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({**payload, "exp": exp}, SECRET_KEY, algorithm=ALGO)

def get_current_user(creds: HTTPAuthorizationCredentials = Depends(_auth)):
    token = creds.credentials
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGO])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

def require_role(role: str):
    def _dep(user=Depends(get_current_user)):
        if user.get("role") != role:
            raise HTTPException(status_code=403, detail="Forbidden")
        return user
    return _dep
