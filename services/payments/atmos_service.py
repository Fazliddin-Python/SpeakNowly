import httpx
from typing import Dict, Any

ATMOS_API_URL = "https://api.atmos.uz/api/v1/invoice/create"
ATMOS_STATUS_URL = "https://api.atmos.uz/api/v1/invoice/status"
ATMOS_MERCHANT_ID = "YOUR_MERCHANT_ID"
ATMOS_SECRET_KEY = "YOUR_SECRET_KEY"

class AtmosService:
    @staticmethod
    async def create_invoice(amount: int, order_id: str, return_url: str, description: str, phone: str) -> Dict[str, Any]:
        payload = {
            "merchant_id": ATMOS_MERCHANT_ID,
            "amount": amount,
            "order_id": order_id,
            "return_url": return_url,
            "description": description,
            "phone": phone,
        }
        headers = {
            "Authorization": f"Bearer {ATMOS_SECRET_KEY}",
            "Content-Type": "application/json"
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(ATMOS_API_URL, json=payload, headers=headers, timeout=30)
            resp.raise_for_status()
            return resp.json()

    @staticmethod
    async def get_invoice_status(order_id: str) -> Dict[str, Any]:
        payload = {
            "merchant_id": ATMOS_MERCHANT_ID,
            "order_id": order_id,
        }
        headers = {
            "Authorization": f"Bearer {ATMOS_SECRET_KEY}",
            "Content-Type": "application/json"
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(ATMOS_STATUS_URL, json=payload, headers=headers, timeout=30)
            resp.raise_for_status()
            return resp.json()