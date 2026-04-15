import aiohttp
import json
import base64
import hashlib
import hmac
from urllib.parse import quote_plus
from typing import Optional, Tuple, Dict, Any
from app.config import load_config

class PaymentAPI:
    """LiqPay payment API client for creating checkout links and verifying status."""

    def __init__(self):
        self.config = load_config()
        self.public_key = self.config.liqpay_public_key
        self.private_key = self.config.liqpay_private_key
        self.sandbox = self.config.liqpay_sandbox

        if not self.public_key or not self.private_key:
            raise RuntimeError("LIQPAY_PUBLIC_KEY and LIQPAY_PRIVATE_KEY must be configured")

        self.api_url = "https://www.liqpay.ua/api/request"
        self.checkout_url = "https://www.liqpay.ua/api/3/checkout"

    def _encode_payload(self, payload: dict) -> str:
        raw_json = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
        return base64.b64encode(raw_json.encode("utf-8")).decode("utf-8")

    def _signature(self, data: str) -> str:
        payload = self.private_key + data + self.private_key
        digest = hashlib.sha1(payload.encode("utf-8")).digest()
        return base64.b64encode(digest).decode("utf-8")

    def _signature_sha3(self, data: str) -> str:
        payload = (self.private_key + data + self.private_key).encode("utf-8")
        digest = hashlib.sha3_256(payload).digest()
        return base64.b64encode(digest).decode("utf-8")

    def verify_callback_signature(self, data: str, signature: str) -> bool:
        if not data or not signature:
            return False
        sig_sha1 = self._signature(data)
        sig_sha3 = self._signature_sha3(data)
        return hmac.compare_digest(signature, sig_sha1) or hmac.compare_digest(signature, sig_sha3)

    def decode_callback_data(self, data: str) -> Optional[Dict[str, Any]]:
        try:
            raw = base64.b64decode(data.encode("utf-8")).decode("utf-8")
            return json.loads(raw)
        except Exception:
            return None

    async def create_payment_link(
        self,
        order_id: int | str,
        amount_minor: int,
        currency: str,
        customer_email: Optional[str],
        order_title: str,
        description: str = "",
    ) -> Tuple[Optional[str], str]:
        """Create a LiqPay checkout link for the order."""
        try:
            amount = amount_minor / 100
            payload = {
                "version": "3",
                "public_key": self.public_key,
                "action": "pay",
                "amount": f"{amount:.2f}",
                "currency": currency.upper(),
                "description": description or f"Payment for order #{order_id}",
                "order_id": str(order_id),
                "language": "en",
                "server_url": f"{self.config.app_url}/webhook/payment",
                "result_url": self.config.app_url,
                "sandbox": 1 if self.sandbox else 0,
            }

            if customer_email:
                payload["email"] = customer_email
            if order_title:
                payload["product_description"] = order_title

            data = self._encode_payload(payload)
            signature = self._signature(data)
            payment_link = f"{self.checkout_url}?data={quote_plus(data)}&signature={quote_plus(signature)}"
            return payment_link, str(order_id)

        except Exception as e:
            print(f"Error creating LiqPay payment link for order {order_id}: {e}")
            return None, ""

    async def verify_payment(self, payment_id: str) -> bool:
        """Verify that the LiqPay payment for the order was completed."""
        if payment_id.startswith("fallback_"):
            return False

        order_id = payment_id
        if payment_id.startswith("liqpay_"):
            order_id = payment_id.split("_", 1)[1]

        payload = {
            "version": "3",
            "public_key": self.public_key,
            "action": "status",
            "order_id": order_id,
            "sandbox": 1 if self.sandbox else 0,
        }

        try:
            data = self._encode_payload(payload)
            signature = self._signature(data)

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.api_url,
                    data={"data": data, "signature": signature},
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status != 200:
                        return False
                    result = await response.json()
                    status = str(result.get("status", "")).lower()
                    return status in {"success", "sandbox"}

        except Exception as e:
            print(f"Error verifying LiqPay payment {payment_id}: {e}")
            return False

    async def get_payment_details(self, payment_id: str) -> Optional[Dict[str, Any]]:
        """Get LiqPay payment details via the status API."""
        if payment_id.startswith("fallback_"):
            return {"status": "pending", "type": "manual"}

        order_id = payment_id
        if payment_id.startswith("liqpay_"):
            order_id = payment_id.split("_", 1)[1]

        payload = {
            "version": "3",
            "public_key": self.public_key,
            "action": "status",
            "order_id": order_id,
            "sandbox": 1 if self.sandbox else 0,
        }

        try:
            data = self._encode_payload(payload)
            signature = self._signature(data)

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.api_url,
                    data={"data": data, "signature": signature},
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status != 200:
                        return None
                    return await response.json()

        except Exception as e:
            print(f"Error getting LiqPay payment details {payment_id}: {e}")
            return None

    async def refund_payment(
        self,
        order_id: str,
        amount_minor: Optional[int] = None,
        currency: str = "USD",
    ) -> Optional[Dict[str, Any]]:
        """Refund a LiqPay payment (full or partial)."""
        payload = {
            "version": "3",
            "public_key": self.public_key,
            "action": "refund",
            "order_id": order_id,
            "currency": currency.upper(),
            "sandbox": 1 if self.sandbox else 0,
        }
        if amount_minor is not None:
            amount = amount_minor / 100
            payload["amount"] = f"{amount:.2f}"

        try:
            data = self._encode_payload(payload)
            signature = self._signature(data)
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.api_url,
                    data={"data": data, "signature": signature},
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status != 200:
                        return None
                    return await response.json()
        except Exception as e:
            print(f"Error refunding LiqPay payment {order_id}: {e}")
            return None


# Global instance
_payment_api = None

def get_payment_api() -> PaymentAPI:
    """Get or create PaymentAPI instance"""
    global _payment_api
    if _payment_api is None:
        _payment_api = PaymentAPI()
    return _payment_api

# Convenience functions
async def create_payment_link(
    order_id: int | str,
    amount_minor: int,
    currency: str,
    customer_email: str | None,
    order_title: str,
) -> Tuple[Optional[str], str]:
    """Create payment link using the payment API"""
    api = get_payment_api()
    return await api.create_payment_link(
        order_id=order_id,
        amount_minor=amount_minor,
        currency=currency,
        customer_email=customer_email,
        order_title=order_title,
    )

async def refund_payment(order_id: str, amount_minor: int | None = None, currency: str = "USD") -> Optional[Dict[str, Any]]:
    api = get_payment_api()
    return await api.refund_payment(order_id=order_id, amount_minor=amount_minor, currency=currency)

async def verify_payment(payment_id: str) -> bool:
    """Verify payment status"""
    api = get_payment_api()
    return await api.verify_payment(payment_id)
