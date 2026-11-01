import logging
from typing import Any, Dict, Optional
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)


class BhapiClient:
    def __init__(self, token: Optional[str] = None, base_url: Optional[str] = None):
        self.token = (token if token is not None else settings.BHAPI_TOKEN) or ""
        self.base_url = (base_url or settings.BHAPI_BASE_URL).rstrip("/")

    def is_configured(self) -> bool:
        return bool(self.token and self.token.strip())

    def _get_headers(self) -> Dict[str, str]:
        return {
            "X-API-Token": self.token.strip(),
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def get_ozon_product(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Fetch Ozon product details by URL using BHAPI v2 (fallback to v1).
        """
        if not self.is_configured():
            logger.warning("BHAPI_TOKEN is not configured! Please provide BHAPI_TOKEN in .env to enable Ozon extraction.")
            return None

        headers = self._get_headers()
        payload = {"url": url, "no_cache": False}

        endpoints = [
            f"{self.base_url}/ozon/api/v2/item/detail-by-url",
            f"{self.base_url}/ozon/api/v1/item/detail-by-url",
        ]

        async with httpx.AsyncClient(timeout=10.0) as client:
            for endpoint in endpoints:
                try:
                    resp = await client.post(endpoint, json=payload, headers=headers)
                    if resp.status_code == 200:
                        data = resp.json()
                        if isinstance(data, dict):
                            item = data.get("data") or data.get("item") or data
                            if isinstance(item, dict) and (item.get("name") or item.get("title") or item.get("sku")):
                                return item
                            return data
                    else:
                        logger.warning(
                            "BHAPI Ozon request to %s returned HTTP %d: %s",
                            endpoint,
                            resp.status_code,
                            resp.text[:200],
                        )
                except Exception as e:
                    logger.warning("BHAPI Ozon request to %s failed: %s", endpoint, e)

        return None

    async def get_wb_product(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Fetch Wildberries product details by URL using BHAPI.
        """
        if not self.is_configured():
            logger.warning("BHAPI_TOKEN is not configured! Please provide BHAPI_TOKEN in .env to enable WB BHAPI extraction.")
            return None

        headers = self._get_headers()

        async with httpx.AsyncClient(timeout=10.0) as client:
            # 1. GET /wb/api/v1/item/by-url?url=...
            try:
                endpoint = f"{self.base_url}/wb/api/v1/item/by-url"
                resp = await client.get(endpoint, params={"url": url}, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    if isinstance(data, dict):
                        return data.get("data") or data.get("item") or data
                else:
                    logger.warning("BHAPI WB GET request returned HTTP %d: %s", resp.status_code, resp.text[:200])
            except Exception as e:
                logger.warning("BHAPI WB GET request failed: %s", e)

            # 2. POST /wb/api/v1/parse/single
            try:
                endpoint = f"{self.base_url}/wb/api/v1/parse/single"
                resp = await client.post(endpoint, json={"url": url}, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    if isinstance(data, dict):
                        return data.get("data") or data.get("item") or data
                else:
                    logger.warning("BHAPI WB POST request returned HTTP %d: %s", resp.status_code, resp.text[:200])
            except Exception as e:
                logger.warning("BHAPI WB POST request failed: %s", e)

        return None

    async def get_aliexpress_product(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Fetch AliExpress product details via BHAPI if supported.
        """
        if not self.is_configured():
            logger.warning("BHAPI_TOKEN is not configured! Please provide BHAPI_TOKEN in .env to enable AliExpress BHAPI extraction.")
            return None

        headers = self._get_headers()
        endpoints = [
            (f"{self.base_url}/aliexpress/api/v1/item/by-url", "GET", {"url": url}, None),
            (f"{self.base_url}/aliexpress/api/v1/item/detail-by-url", "POST", None, {"url": url}),
        ]

        async with httpx.AsyncClient(timeout=10.0) as client:
            for endpoint, method, params, payload in endpoints:
                try:
                    if method == "GET":
                        resp = await client.get(endpoint, params=params, headers=headers)
                    else:
                        resp = await client.post(endpoint, json=payload, headers=headers)
                    if resp.status_code == 200:
                        data = resp.json()
                        if isinstance(data, dict):
                            return data.get("data") or data.get("item") or data
                except Exception:
                    pass

        return None


bhapi_client = BhapiClient()
