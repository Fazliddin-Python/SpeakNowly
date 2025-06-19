from decouple import config
import time
import httpx
from typing import Dict, Any
from pydantic import BaseModel, Field

class AtmosAuthResponse(BaseModel):
    access_token: str
    expires_in: int

class AtmosCreateResponse(BaseModel):
    code: str = Field(..., alias="result.code")
    description: str = Field(..., alias="result.description")
    transaction_id: int
    store_transaction: Dict[str, Any]

class AtmosService:
    """
    Corrected Atmos client for pay/create and pay/status.
    Token endpoint is NOT under /merchant.
    """
    def __init__(self):
        self.base_url = "https://partner.atmos.uz"
        self.merchant_url = f"{self.base_url}/merchant"
        self._client = httpx.AsyncClient(timeout=10)

        self.store_id = config("ATMOS_MERCHANT_ID")
        self.key = config("ATMOS_CONSUMER_KEY")
        self.secret = config("ATMOS_CONSUMER_SECRET")

        self._token = None
        self._token_expiry = 0

    async def _ensure_token(self):
        now = time.time()
        if self._token and now < self._token_expiry:
            return
        # Correct endpoint: /oauth/token (NOT under /merchant)
        resp = await self._client.post(
            f"{self.base_url}/oauth/token",
            data={"grant_type": "client_credentials"},
            auth=(self.key, self.secret),
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        resp.raise_for_status()
        auth = AtmosAuthResponse(**resp.json())
        self._token = auth.access_token
        self._token_expiry = now + auth.expires_in - 5

    async def create_payment(self, amount: int, account: str, lang: str = "ru") -> AtmosCreateResponse:
        await self._ensure_token()
        payload = {
            "amount": amount,
            "account": account,
            "store_id": self.store_id,
            "lang": lang
        }
        headers = {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json"
        }
        resp = await self._client.post(f"{self.merchant_url}/pay/create", json=payload, headers=headers)
        resp.raise_for_status()
        return AtmosCreateResponse.parse_obj(resp.json())

    async def get_status(self, transaction_id: int) -> Dict[str, Any]:
        await self._ensure_token()
        payload = {
            "transaction_id": transaction_id,
            "store_id": self.store_id
        }
        headers = {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json"
        }
        resp = await self._client.post(f"{self.merchant_url}/pay/status", json=payload, headers=headers)
        resp.raise_for_status()
        return resp.json()

    async def close(self):
        await self._client.aclose()

# Singleton instance
atm = AtmosService()
