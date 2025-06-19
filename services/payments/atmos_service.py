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
    Simple Atmos client for merchant pay/create and pay/status.
    """
    def __init__(self):
        # Base URL for ATMOS merchant endpoints is hardcoded as per docs
        self._client = httpx.AsyncClient(
            base_url="https://partner.atmos.uz/merchant", timeout=10
        )
        # Store identifier provided by ATMOS
        self.store_id = config('ATMOS_MERCHANT_ID')
        # OAuth2 client credentials
        self.key = config('ATMOS_CONSUMER_KEY')
        self.secret = config('ATMOS_CONSUMER_SECRET')
        self._token = None
        self._token_expiry = 0

    async def _ensure_token(self):
        now = time.time()
        if self._token and now < self._token_expiry:
            return
        # Token endpoint: POST /oauth/token
        resp = await self._client.post(
            '/oauth/token',
            data={'grant_type': 'client_credentials'},
            auth=(self.key, self.secret),
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        resp.raise_for_status()
        auth = AtmosAuthResponse(**resp.json())
        self._token = auth.access_token
        self._token_expiry = now + auth.expires_in - 5

    async def create_payment(self, amount: int, account: str, lang: str = 'ru') -> AtmosCreateResponse:
        await self._ensure_token()
        payload = {
            'amount': amount,
            'account': account,
            'store_id': self.store_id,
            'lang': lang
        }
        headers = {'Authorization': f'Bearer {self._token}', 'Content-Type': 'application/json'}
        # Endpoint: POST /pay/create
        resp = await self._client.post('/pay/create', json=payload, headers=headers)
        resp.raise_for_status()
        return AtmosCreateResponse.parse_obj(resp.json())

    async def get_status(self, transaction_id: int) -> Dict[str, Any]:
        await self._ensure_token()
        payload = {
            'transaction_id': transaction_id,
            'store_id': self.store_id
        }
        headers = {'Authorization': f'Bearer {self._token}', 'Content-Type': 'application/json'}
        # Endpoint: POST /pay/status
        resp = await self._client.post('/pay/status', json=payload, headers=headers)
        resp.raise_for_status()
        return resp.json()

    async def close(self):
        await self._client.aclose()

# Singleton instance
atm = AtmosService()
