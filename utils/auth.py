from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError, ExpiredSignatureError
from datetime import datetime, timedelta
from config import SECRET_KEY, ALGORITHM

security = HTTPBearer()

def create_access_token(data: dict, expires_delta: timedelta = timedelta(days=7)) -> str:
    """
    Generate a JWT access token.
    """
    to_encode = data.copy()
    to_encode.update({"exp": (datetime.utcnow() + expires_delta), "sub": str(data["sub"])})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str) -> dict:
    """
    Decode a JWT token and return the payload.
    """
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    Dependency that extracts user information from the token.
    """
    payload = decode_access_token(credentials.credentials)
    user_id = payload.get("sub")
    email = payload.get("email")
    if user_id is None or email is None:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    return {"user_id": user_id, "email": email}
