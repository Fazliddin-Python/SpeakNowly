from datetime import datetime, timezone, timedelta
from typing import Optional, TypedDict

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError, ExpiredSignatureError

from config import SECRET_KEY, ALGORITHM
from models.users.users import User


class TokenPayload(TypedDict):
    sub: str
    email: str
    exp: int


security = HTTPBearer()


def create_access_token(
    subject: str,
    email: str,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a signed JWT access token with an expiration time.
    """
    if expires_delta is None:
        expires_delta = timedelta(days=7)

    expire = datetime.now(timezone.utc) + expires_delta
    expire_timestamp = int(expire.timestamp())

    payload = {"sub": subject, "email": email, "exp": expire_timestamp}

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(
    subject: str,
    email: str,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a signed JWT refresh token with a longer expiration.
    """
    if expires_delta is None:
        expires_delta = timedelta(days=30)
    expire = datetime.now(timezone.utc) + expires_delta
    expire_timestamp = int(expire.timestamp())
    payload = {"sub": subject, "email": email, "exp": expire_timestamp, "type": "refresh"}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> TokenPayload:
    """
    Decode and validate the JWT access token.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        sub = payload.get("sub")
        email = payload.get("email")

        if not sub or not email:
            raise HTTPException(status_code=401, detail="Invalid token payload")

        return {"sub": sub, "email": email, "exp": payload["exp"]}

    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    FastAPI dependency to extract current user from the token.
    """
    payload = decode_access_token(credentials.credentials)
    user_id = payload["sub"]
    user = await User.get(id=user_id)
    return user
