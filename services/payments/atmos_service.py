import httpx
from typing import Dict, Any

# Atmos test data
ATMOS_API_URL = "https://api-sandbox.atmos.uz/api/v1/invoice/create"
ATMOS_STATUS_URL = "https://api-sandbox.atmos.uz/api/v1/invoice/status"
ATMOS_MERCHANT_ID = "8157"  # store_id
ATMOS_CONSUMER_KEY = "USQoUyCLfe2kHfc9tJs97amTRoEa"
ATMOS_CONSUMER_SECRET = "EtWplLvZpfvDMStf5PstH2hn4qQa"

class AtmosService:
    @staticmethod
    async def create_invoice(amount: int, order_id: str, return_url: str, description: str, phone: str) -> Dict[str, Any]:
        """
        Create an invoice in the Atmos system.
        """
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
        """
        Check the status of an invoice in the Atmos system.
        """
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