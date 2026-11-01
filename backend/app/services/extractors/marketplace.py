import json
import logging
import re
from typing import Any, Dict, Optional
from urllib.parse import urlparse
import httpx
from bs4 import BeautifulSoup

from app.schemas.link import SiteType
from app.services.extractors.base import BaseExtractor, ExtractedMetadata
from app.services.extractors.bhapi import BhapiClient, bhapi_client

logger = logging.getLogger(__name__)

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36 LinkSaver/1.0"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
}


def _format_price(raw_price: Any) -> Optional[str]:
    """Format numeric or string price into a readable rubles string."""
    if raw_price is None:
        return None
    try:
        if isinstance(raw_price, (int, float)):
            val = int(raw_price)
            # If WB kopecks (e.g. 150000 -> 1500)
            if val > 1000000:
                val = val // 100
            return f"{val:,}".replace(",", " ") + " ₽"
        clean = str(raw_price).strip()
        if clean.isdigit():
            val = int(clean)
            if val > 1000000:
                val = val // 100
            return f"{val:,}".replace(",", " ") + " ₽"
        return clean
    except Exception:
        return str(raw_price)


def _extract_json_ld(soup: BeautifulSoup) -> Dict[str, Any]:
    """Parse schema.org Product from application/ld+json scripts."""
    for script in soup.find_all("script", type="application/ld+json"):
        if not script.string:
            continue
        try:
            data = json.loads(script.string.strip())
            items = data if isinstance(data, list) else [data]
            for item in items:
                if isinstance(item, dict):
                    item_type = str(item.get("@type", "")).lower()
                    if "product" in item_type:
                        return item
        except Exception:
            continue
    return {}


class OzonExtractor(BaseExtractor):
    def __init__(self, client: Optional[BhapiClient] = None):
        self.client = client or bhapi_client

    async def extract(self, url: str) -> ExtractedMetadata:
        parsed = urlparse(url)
        sku_match = re.search(r'/product/[^/]*?-?(\d+)/?', parsed.path) or re.search(r'/product/(\d+)', parsed.path)
        sku = sku_match.group(1) if sku_match else None

        fallback_title = f"Ozon Товар {f'({sku})' if sku else ''}".strip()
        fallback_desc = "Товар на маркетплейсе Ozon."

        # 1. Try BHAPI if configured
        if self.client.is_configured():
            try:
                bh_data = await self.client.get_ozon_product(url)
                if bh_data:
                    title = bh_data.get("name") or bh_data.get("title") or bh_data.get("product_name")
                    price = (
                        bh_data.get("price")
                        or (bh_data.get("price_info") or {}).get("price")
                        or bh_data.get("card_price")
                        or bh_data.get("final_price")
                    )
                    brand = bh_data.get("brand") or bh_data.get("brand_name")
                    rating = bh_data.get("rating") or bh_data.get("review_rating")
                    reviews_count = bh_data.get("reviews_count") or bh_data.get("feedbacks_count")
                    desc = bh_data.get("description") or bh_data.get("short_description") or ""

                    details = []
                    formatted_price = _format_price(price)
                    if formatted_price:
                        details.append(f"Цена: {formatted_price}")
                    if brand:
                        details.append(f"Бренд: {brand}")
                    if rating:
                        rating_str = f"★ {rating}"
                        if reviews_count:
                            rating_str += f" ({reviews_count} отзывов)"
                        details.append(rating_str)

                    description_parts = []
                    if details:
                        description_parts.append(" | ".join(details))
                    if desc:
                        clean_desc = re.sub(r'<[^>]+>', ' ', str(desc)).strip()
                        description_parts.append(clean_desc[:300] + ("..." if len(clean_desc) > 300 else ""))

                    final_desc = " \n".join(description_parts) or fallback_desc

                    return ExtractedMetadata(
                        title=str(title).strip() if title else fallback_title,
                        description=final_desc,
                        site_type=SiteType.ozon,
                    )
            except Exception as e:
                logger.warning("Error processing BHAPI Ozon product: %s", e)

        # 2. Fallback to OpenGraph / HTML extraction
        try:
            async with httpx.AsyncClient(timeout=5.0, follow_redirects=True) as http_c:
                resp = await http_c.get(url, headers=DEFAULT_HEADERS)
                if resp.status_code < 400:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    json_ld = _extract_json_ld(soup)

                    title = None
                    if json_ld.get("name"):
                        title = str(json_ld["name"]).strip()
                    if not title:
                        og_title = soup.find("meta", property="og:title") or soup.find("meta", attrs={"name": "og:title"})
                        if og_title and og_title.get("content"):
                            title = og_title["content"].strip()
                    if not title and soup.find("title") and soup.find("title").string:
                        title = soup.find("title").string.strip()

                    desc = None
                    if json_ld.get("description"):
                        desc = str(json_ld["description"]).strip()
                    if not desc:
                        og_desc = soup.find("meta", property="og:description") or soup.find("meta", attrs={"name": "og:description"})
                        if og_desc and og_desc.get("content"):
                            desc = og_desc["content"].strip()

                    # Check price in json-ld offers
                    offers = json_ld.get("offers") or {}
                    if isinstance(offers, list) and offers:
                        offers = offers[0]
                    price_val = offers.get("price") if isinstance(offers, dict) else None

                    details = []
                    if price_val:
                        details.append(f"Цена: {_format_price(price_val)}")
                    brand = json_ld.get("brand")
                    if isinstance(brand, dict):
                        brand = brand.get("name")
                    if brand:
                        details.append(f"Бренд: {brand}")

                    final_desc = " | ".join(details)
                    if desc:
                        final_desc = f"{final_desc} \n{desc}" if final_desc else desc

                    return ExtractedMetadata(
                        title=title or fallback_title,
                        description=final_desc or fallback_desc,
                        site_type=SiteType.ozon,
                    )
        except Exception as e:
            logger.warning("Fallback Ozon extractor failed: %s", e)

        return ExtractedMetadata(
            title=fallback_title,
            description=fallback_desc,
            site_type=SiteType.ozon,
        )


class WildberriesExtractor(BaseExtractor):
    def __init__(self, client: Optional[BhapiClient] = None):
        self.client = client or bhapi_client

    async def extract(self, url: str) -> ExtractedMetadata:
        article_match = re.search(r'/catalog/(\d+)', url) or re.search(r'nm=(\d+)', url) or re.search(r'/product/(\d+)', url)
        article = article_match.group(1) if article_match else None

        fallback_title = f"Wildberries Товар {f'(арт. {article})' if article else ''}".strip()
        fallback_desc = "Товар на маркетплейсе Wildberries."

        # 1. Try BHAPI if configured
        if self.client.is_configured():
            try:
                bh_data = await self.client.get_wb_product(url)
                if bh_data:
                    title = bh_data.get("imt_name") or bh_data.get("name") or bh_data.get("title") or bh_data.get("goods_name")
                    price = bh_data.get("price") or bh_data.get("sale_price_u") or bh_data.get("final_price")
                    brand = bh_data.get("brand") or bh_data.get("brand_name")
                    rating = bh_data.get("review_rating") or bh_data.get("rating")
                    feedbacks = bh_data.get("feedbacks_count") or bh_data.get("reviews_count")
                    desc = bh_data.get("description") or ""

                    details = []
                    formatted_price = _format_price(price)
                    if formatted_price:
                        details.append(f"Цена: {formatted_price}")
                    if brand:
                        details.append(f"Бренд: {brand}")
                    if rating:
                        rating_str = f"★ {rating}"
                        if feedbacks:
                            rating_str += f" ({feedbacks} отзывов)"
                        details.append(rating_str)

                    description_parts = []
                    if details:
                        description_parts.append(" | ".join(details))
                    if desc:
                        clean_desc = re.sub(r'<[^>]+>', ' ', str(desc)).strip()
                        description_parts.append(clean_desc[:300] + ("..." if len(clean_desc) > 300 else ""))

                    final_desc = " \n".join(description_parts) or fallback_desc

                    return ExtractedMetadata(
                        title=str(title).strip() if title else fallback_title,
                        description=final_desc,
                        site_type=SiteType.wildberries,
                    )
            except Exception as e:
                logger.warning("Error processing BHAPI Wildberries product: %s", e)

        # 2. Try WB public API using article if available
        if article:
            try:
                wb_api_url = f"https://card.wb.ru/cards/v2/detail?appType=1&curr=rub&dest=-1257786&nm={article}"
                async with httpx.AsyncClient(timeout=4.0) as http_c:
                    resp = await http_c.get(wb_api_url, headers=DEFAULT_HEADERS)
                    if resp.status_code == 200:
                        wb_json = resp.json()
                        products = (wb_json.get("data") or {}).get("products") or []
                        if products and isinstance(products, list):
                            prod = products[0]
                            name = prod.get("name")
                            brand = prod.get("brand")
                            sizes = prod.get("sizes") or []
                            price = None
                            if sizes and isinstance(sizes, list):
                                price = (sizes[0].get("price") or {}).get("total")
                            if not price:
                                price = prod.get("salePriceU") or prod.get("priceU")

                            rating = prod.get("rating") or prod.get("reviewRating")
                            feedbacks = prod.get("feedbacks")

                            title = f"{name} {f'– {brand}' if brand else ''}".strip()
                            details = []
                            if price:
                                details.append(f"Цена: {_format_price(price // 100 if price > 100000 else price)}")
                            if brand:
                                details.append(f"Бренд: {brand}")
                            if rating:
                                r_str = f"★ {rating}"
                                if feedbacks:
                                    r_str += f" ({feedbacks} отзывов)"
                                details.append(r_str)

                            final_desc = f"Wildberries (арт. {article}) | " + " | ".join(details)
                            return ExtractedMetadata(
                                title=title or fallback_title,
                                description=final_desc,
                                site_type=SiteType.wildberries,
                            )
            except Exception as e:
                logger.warning("WB Public API fallback failed: %s", e)

        # 3. Fallback to OpenGraph / HTML extraction
        try:
            async with httpx.AsyncClient(timeout=4.0, follow_redirects=True) as http_c:
                resp = await http_c.get(url, headers=DEFAULT_HEADERS)
                if resp.status_code < 400:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    og_title = soup.find("meta", property="og:title") or soup.find("meta", attrs={"name": "og:title"})
                    og_desc = soup.find("meta", property="og:description") or soup.find("meta", attrs={"name": "og:description"})

                    title = og_title.get("content").strip() if og_title and og_title.get("content") else None
                    desc = og_desc.get("content").strip() if og_desc and og_desc.get("content") else None

                    return ExtractedMetadata(
                        title=title or fallback_title,
                        description=desc or fallback_desc,
                        site_type=SiteType.wildberries,
                    )
        except Exception:
            pass

        return ExtractedMetadata(
            title=fallback_title,
            description=fallback_desc,
            site_type=SiteType.wildberries,
        )


class AliExpressExtractor(BaseExtractor):
    def __init__(self, client: Optional[BhapiClient] = None):
        self.client = client or bhapi_client

    async def extract(self, url: str) -> ExtractedMetadata:
        item_match = re.search(r'/item/(\d+)', url)
        item_id = item_match.group(1) if item_match else None

        fallback_title = f"AliExpress Товар {f'({item_id})' if item_id else ''}".strip()
        fallback_desc = "Товар на торговой площадке AliExpress."

        # 1. Try BHAPI if configured
        if self.client.is_configured():
            try:
                bh_data = await self.client.get_aliexpress_product(url)
                if bh_data:
                    title = bh_data.get("name") or bh_data.get("title") or bh_data.get("subject")
                    price = bh_data.get("price") or bh_data.get("final_price") or bh_data.get("sale_price")
                    store = bh_data.get("store_name") or bh_data.get("seller")
                    rating = bh_data.get("rating")
                    orders = bh_data.get("orders") or bh_data.get("sales_count")
                    desc = bh_data.get("description") or ""

                    details = []
                    formatted_price = _format_price(price)
                    if formatted_price:
                        details.append(f"Цена: {formatted_price}")
                    if store:
                        details.append(f"Магазин: {store}")
                    if rating:
                        details.append(f"★ {rating}")
                    if orders:
                        details.append(f"{orders} заказов")

                    description_parts = []
                    if details:
                        description_parts.append(" | ".join(details))
                    if desc:
                        clean_desc = re.sub(r'<[^>]+>', ' ', str(desc)).strip()
                        description_parts.append(clean_desc[:300] + ("..." if len(clean_desc) > 300 else ""))

                    final_desc = " \n".join(description_parts) or fallback_desc

                    return ExtractedMetadata(
                        title=str(title).strip() if title else fallback_title,
                        description=final_desc,
                        site_type=SiteType.aliexpress,
                    )
            except Exception as e:
                logger.warning("Error processing BHAPI AliExpress product: %s", e)

        # 2. Fallback to OpenGraph / HTML scraping
        try:
            async with httpx.AsyncClient(timeout=5.0, follow_redirects=True) as http_c:
                resp = await http_c.get(url, headers=DEFAULT_HEADERS)
                if resp.status_code < 400:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    json_ld = _extract_json_ld(soup)

                    title = None
                    if json_ld.get("name"):
                        title = str(json_ld["name"]).strip()
                    if not title:
                        og_title = soup.find("meta", property="og:title") or soup.find("meta", attrs={"name": "og:title"})
                        if og_title and og_title.get("content"):
                            title = og_title["content"].strip()
                    if not title and soup.find("title") and soup.find("title").string:
                        title = soup.find("title").string.strip()

                    desc = None
                    if json_ld.get("description"):
                        desc = str(json_ld["description"]).strip()
                    if not desc:
                        og_desc = soup.find("meta", property="og:description") or soup.find("meta", attrs={"name": "og:description"})
                        if og_desc and og_desc.get("content"):
                            desc = og_desc["content"].strip()

                    offers = json_ld.get("offers") or {}
                    if isinstance(offers, list) and offers:
                        offers = offers[0]
                    price_val = offers.get("price") if isinstance(offers, dict) else None

                    details = []
                    if price_val:
                        details.append(f"Цена: {_format_price(price_val)}")
                    brand = json_ld.get("brand")
                    if isinstance(brand, dict):
                        brand = brand.get("name")
                    if brand:
                        details.append(f"Бренд: {brand}")

                    final_desc = " | ".join(details)
                    if desc:
                        final_desc = f"{final_desc} \n{desc}" if final_desc else desc

                    return ExtractedMetadata(
                        title=title or fallback_title,
                        description=final_desc or fallback_desc,
                        site_type=SiteType.aliexpress,
                    )
        except Exception as e:
            logger.warning("Fallback AliExpress extractor failed: %s", e)

        return ExtractedMetadata(
            title=fallback_title,
            description=fallback_desc,
            site_type=SiteType.aliexpress,
        )
