import base64
import time
import httpx
from decouple import config
from typing import Dict, Any
from pydantic import BaseModel

class AtmosAuthResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

class AtmosCreateResponse(BaseModel):
    result: Dict[str, Any]
    transaction_id: int
    store_transaction: Dict[str, Any]

class AtmosService:
    """
    Atmos API client (token, create, status).
    """
    def __init__(self):
        self.base_url = "https://partner.atmos.uz"
        self.store_id = config("ATMOS_MERCHANT_ID")
        self.key = config("ATMOS_CONSUMER_KEY")
        self.secret = config("ATMOS_CONSUMER_SECRET")
        self._token = None
        self._token_expiry = 0
        self._client = httpx.AsyncClient(timeout=10)

    async def _ensure_token(self):
        now = time.time()
        if self._token and now < self._token_expiry:
            return

        credentials = f"{self.key}:{self.secret}".encode("utf-8")
        basic_auth = base64.b64encode(credentials).decode("utf-8")

        headers = {
            "Authorization": f"Basic {basic_auth}",
            "Content-Type": "application/x-www-form-urlencoded"
        }

        data = {"grant_type": "client_credentials"}

        resp = await self._client.post(f"{self.base_url}/token", data=data, headers=headers)
        resp.raise_for_status()

        auth = AtmosAuthResponse(**resp.json())
        self._token = auth.access_token
        self._token_expiry = now + auth.expires_in - 5

    async def create_payment(self, amount: int, account: str, lang: str = "ru") -> AtmosCreateResponse:
        await self._ensure_token()

        headers = {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json"
        }

        payload = {
            "amount": amount,
            "account": account,
            "store_id": self.store_id,
            "lang": lang
        }

        resp = await self._client.post(f"{self.base_url}/pay/create", json=payload, headers=headers)
        resp.raise_for_status()

        return AtmosCreateResponse(**resp.json())

    async def get_status(self, transaction_id: int) -> Dict[str, Any]:
        await self._ensure_token()

        headers = {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json"
        }

        payload = {
            "transaction_id": transaction_id,
            "store_id": self.store_id
        }

        resp = await self._client.post(f"{self.base_url}/pay/status", json=payload, headers=headers)
        resp.raise_for_status()
        return resp.json()

    async def close(self):
        await self._client.aclose()

# Singleton instance
atm = AtmosService()
