from typing import Literal

from fastapi import HTTPException
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token

from utils.auth.apple_auth import decode_apple_id_token
from utils.auth.auth import create_access_token
from models.users.users import User


async def oauth2_sign_in(
    token: str,
    auth_type: Literal["google", "apple"],
    client_id: str
) -> dict:
    """
    Authenticate user via Google or Apple OAuth2, returning an access token.
    """
    if auth_type == "google":
        try:
            payload = google_id_token.verify_oauth2_token(token, google_requests.Request(), client_id)
            email = payload.get("email")
            if not email:
                raise HTTPException(status_code=403, detail="Email not provided by Google token")
        except ValueError:
            raise HTTPException(status_code=403, detail="Invalid Google ID token")

    elif auth_type == "apple":
        try:
            payload = decode_apple_id_token(token, client_id)
            email = payload.get("email")
            if not email:
                raise HTTPException(status_code=403, detail="Email not provided by Apple token")
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(status_code=403, detail="Invalid Apple ID token")

    else:
        raise HTTPException(status_code=400, detail="Unsupported authentication provider")

    user, _ = await User.get_or_create(email=email)
    access_token = create_access_token(subject=str(user.id), email=user.email)
    return {"access_token": access_token}