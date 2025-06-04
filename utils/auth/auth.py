from datetime import datetime, timezone, timedelta
from typing import Optional, TypedDict, Union

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError, ExpiredSignatureError

from config import SECRET_KEY, ALGORITHM
from models.users.users import User

class TokenPayload(TypedDict, total=True):
    sub: str
    email: str
    exp: int
    type: Optional[str]

security = HTTPBearer()

def create_access_token(
    subject: str,
    email: str,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a signed JWT access token that expires after a specified time.
    """
    if expires_delta is None:
        expires_delta = timedelta(days=1)
    expire = datetime.now(timezone.utc) + expires_delta
    expire_timestamp = int(expire.timestamp())
    payload = {"sub": subject, "email": email, "exp": expire_timestamp, "type": "access"}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(
    subject: str,
    email: str,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a signed JWT refresh token that expires after a specified time.
    """
    if expires_delta is None:
        expires_delta = timedelta(days=30)
    expire = datetime.now(timezone.utc) + expires_delta
    expire_timestamp = int(expire.timestamp())
    payload = {"sub": subject, "email": email, "exp": expire_timestamp, "type": "refresh"}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(
    token: str,
    *,
    require_refresh: bool = False
) -> TokenPayload:
    """
    Decode and validate a JWT token.
    If require_refresh is True, ensure the token is a refresh token.
    Otherwise, expect an access token.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    sub = payload.get("sub")
    email = payload.get("email")
    token_type = payload.get("type", "access")
    if not sub or not email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    if require_refresh:
        if token_type != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is not a refresh token")
    else:
        if token_type != "access":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is not an access token")

    return {"sub": sub, "email": email, "exp": payload["exp"], "type": token_type}

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """
    FastAPI dependency: extract the current user from the access token.
    """
    token_str = credentials.credentials
    payload = decode_access_token(token_str, require_refresh=False)
    user_id = payload["sub"]
    user = await User.get_or_none(id=user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user
