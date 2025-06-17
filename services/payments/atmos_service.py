from decouple import config
import httpx
from typing import Dict, Any

ATMOS_API_URL = config("ATMOS_API_URL")
ATMOS_STATUS_URL = config("ATMOS_STATUS_URL")
ATMOS_MERCHANT_ID = config("ATMOS_MERCHANT_ID")
ATMOS_CONSUMER_KEY = config("ATMOS_CONSUMER_KEY")
ATMOS_CONSUMER_SECRET = config("ATMOS_CONSUMER_SECRET")

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
            "Authorization": f"Bearer {ATMOS_CONSUMER_SECRET}",
            "Content-Type": "application/json"
        }
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(ATMOS_API_URL, json=payload, headers=headers, timeout=30)
                resp.raise_for_status()
                return resp.json()
            except httpx.HTTPStatusError as e:
                raise Exception(f"Failed to create invoice: {e.response.text}")

    @staticmethod
    async def get_invoice_status(order_id: str) -> Dict[str, Any]:
        payload = {
            "merchant_id": ATMOS_MERCHANT_ID,
            "order_id": order_id,
        }
        headers = {
            "Authorization": f"Bearer {ATMOS_CONSUMER_SECRET}",
            "Content-Type": "application/json"
        }
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(ATMOS_STATUS_URL, json=payload, headers=headers, timeout=30)
                resp.raise_for_status()
                return resp.json()
            except httpx.HTTPStatusError as e:
                raise Exception(f"Failed to get invoice status: {e.response.text}")