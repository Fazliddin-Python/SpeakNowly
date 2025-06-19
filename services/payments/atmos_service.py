import base64
import time
from types import SimpleNamespace
import httpx
from decouple import config
from pydantic import BaseModel, Field

class AtmosAuthResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

class AtmosCreateResponse(BaseModel):
    result: dict
    transaction_id: int = Field(..., alias='transactionId')
    store_transaction: dict = Field(..., alias='storeTransaction')

class AtmosService:
    """Atmos API client: handles token retrieval, payment creation, and status checks

    Environment variables required:
      - ATMOS_MERCHANT_ID: your Atmos merchant (store) ID
      - ATMOS_CONSUMER_KEY: your Atmos OAuth client key
      - ATMOS_CONSUMER_SECRET: your Atmos OAuth client secret
    """
    def __init__(self):
        self.token_url = "https://partner.atmos.uz/token"
        self.api_url = "https://partner.atmos.uz/merchant"
        self.store_id = config("ATMOS_MERCHANT_ID")
        self.key = config("ATMOS_CONSUMER_KEY")
        self.secret = config("ATMOS_CONSUMER_SECRET")
        self._token = None
        self._token_expiry = 0
        self._client = httpx.AsyncClient(timeout=10)

    async def _ensure_token(self):
        """Retrieve and cache OAuth token until expiry"""
        now = time.time()
        if self._token and now < self._token_expiry:
            return

        credentials = f"{self.key}:{self.secret}".encode()
        basic_auth = base64.b64encode(credentials).decode()
        headers = {
            "Authorization": f"Basic {basic_auth}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {"grant_type": "client_credentials"}

        response = await self._client.post(self.token_url, data=data, headers=headers)
        response.raise_for_status()

        auth_data = AtmosAuthResponse(**response.json())
        self._token = auth_data.access_token
        # expire slightly before actual expiry to avoid edge cases
        self._token_expiry = now + auth_data.expires_in - 5

    async def create_payment(self, amount: int, account: str, lang: str = "ru") -> AtmosCreateResponse:
        """Create a payment transaction and return the API response model"""
        await self._ensure_token()
        headers = {"Authorization": f"Bearer {self._token}", "Content-Type": "application/json"}
        payload = {"amount": amount, "account": account, "store_id": self.store_id, "lang": lang}

        response = await self._client.post(
            f"{self.api_url}/pay/create", json=payload, headers=headers
        )
        response.raise_for_status()
        return AtmosCreateResponse(**response.json())

    async def get_status(self, transaction_id: int) -> dict:
        """Fetch the current status of a payment transaction"""
        await self._ensure_token()
        headers = {"Authorization": f"Bearer {self._token}", "Content-Type": "application/json"}
        payload = {"transaction_id": transaction_id, "store_id": self.store_id}

        response = await self._client.post(
            f"{self.api_url}/pay/status", json=payload, headers=headers
        )
        response.raise_for_status()
        return response.json()

    async def create_invoice(self, amount: int, account: str, redirect_link: str | None = None, lang: str = "ru"):
        """Generate an invoice and return a namespace with payment_id and redirect URL"""
        payment_resp = await self.create_payment(amount, account, lang)
        tx_id = payment_resp.transaction_id
        base_url = "https://checkout.pays.uz/invoice/get"
        redirect_url = f"{base_url}?storeId={self.store_id}&transactionId={tx_id}"
        if redirect_link:
            redirect_url += f"&redirectLink={redirect_link}"
        return SimpleNamespace(payment_id=tx_id, url=redirect_url)

    async def close(self):
        """Close the underlying HTTP client"""
        await self._client.aclose()

# Singleton instance for reuse
atm = AtmosService()