from typing import Literal
from fastapi import HTTPException
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from utils.auth.apple_auth import decode_apple_id_token
from utils.auth.auth import create_access_token, create_refresh_token
from models.users.users import User
from config import GOOGLE_CLIENT_ID
import asyncio

async def oauth2_sign_in(
    token: str,
    auth_type: Literal["google", "apple"],
    client_id: str = None
) -> dict:
    """
    Authenticate user via Google or Apple OAuth2, registering if needed, and return access and refresh tokens.
    """
    email = None

    if auth_type == "google":
        try:
            # Run sync verification in executor to avoid blocking event loop
            payload = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: google_id_token.verify_oauth2_token(token, google_requests.Request(), GOOGLE_CLIENT_ID)
            )
            email = payload.get("email")
            if not email:
                raise HTTPException(status_code=403, detail="Email not provided by Google token")
        except ValueError:
            raise HTTPException(status_code=403, detail="Invalid Google ID token")

    elif auth_type == "apple":
        try:
            payload = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: decode_apple_id_token(token, client_id)
            )
            email = payload.get("email")
            if not email:
                raise HTTPException(status_code=403, detail="Email not provided by Apple token")
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(status_code=403, detail="Invalid Apple ID token")

    else:
        raise HTTPException(status_code=400, detail="Unsupported authentication provider")

    user, created = await User.get_or_create(email=email)
    if created:
        user.is_verified = True
        user.is_active = True
        await user.save()

    access_token = await create_access_token(subject=str(user.id), email=user.email)
    refresh_token = await create_refresh_token(subject=str(user.id), email=user.email)
    return {"access_token": access_token, "refresh_token": refresh_token}