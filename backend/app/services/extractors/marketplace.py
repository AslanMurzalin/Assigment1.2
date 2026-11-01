import json
import logging
import re
from typing import Any, Dict, List, Optional
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
            if val > 1000000:
                val = val // 100
            return f"{val:,}".replace(",", " ") + " ₽"
        clean = str(raw_price).strip().replace(" ", "").replace("₽", "").replace("руб.", "").replace("руб", "")
        if clean.isdigit():
            val = int(clean)
            if val > 1000000:
                val = val // 100
            return f"{val:,}".replace(",", " ") + " ₽"
        return str(raw_price).strip()
    except Exception:
        return str(raw_price)


def _extract_image_from_dict(data: Dict[str, Any]) -> Optional[str]:
    """Find the best product photo URL from a dictionary."""
    candidates = [
        data.get("main_image"),
        data.get("image"),
        data.get("primary_image"),
        data.get("photo"),
        data.get("cover"),
        data.get("thumbnail"),
    ]
    for c in candidates:
        if isinstance(c, str) and c.startswith("http"):
            return c

    images = data.get("images") or data.get("photos") or data.get("gallery")
    if isinstance(images, list) and images:
        first = images[0]
        if isinstance(first, str) and first.startswith("http"):
            return first
        if isinstance(first, dict):
            for k in ["url", "src", "link", "big", "original"]:
                val = first.get(k)
                if isinstance(val, str) and val.startswith("http"):
                    return val
    return None


def _extract_specs_from_dict(data: Dict[str, Any]) -> Dict[str, str]:
    """Extract structured characteristics / specifications from a dictionary."""
    specs: Dict[str, str] = {}

    # Common direct fields
    if data.get("brand") or data.get("brand_name"):
        specs["Бренд"] = str(data.get("brand") or data.get("brand_name"))
    if data.get("model"):
        specs["Модель"] = str(data["model"])
    if data.get("color") or data.get("color_name"):
        specs["Цвет"] = str(data.get("color") or data.get("color_name"))
    if data.get("category") or data.get("category_name"):
        specs["Категория"] = str(data.get("category") or data.get("category_name"))

    chars = (
        data.get("characteristics")
        or data.get("attributes")
        or data.get("parameters")
        or data.get("options")
        or data.get("properties")
    )
    if isinstance(chars, dict):
        for k, v in chars.items():
            if isinstance(v, (str, int, float)) and v:
                specs[str(k).strip()] = str(v).strip()
    elif isinstance(chars, list):
        for item in chars:
            if isinstance(item, dict):
                k = item.get("name") or item.get("key") or item.get("title") or item.get("param_name")
                v = item.get("value") or item.get("val") or item.get("values")
                if isinstance(v, list) and v:
                    v = ", ".join(str(x) for x in v)
                if k and v:
                    specs[str(k).strip()] = str(v).strip()

    return specs


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


def _get_wb_cdn_image(article: str) -> Optional[str]:
    """Construct WB CDN basket image URL based on NM ID."""
    try:
        nm = int(article)
        vol = nm // 100000
        part = nm // 1000
        if 0 <= vol <= 143:
            basket = 1
        elif 144 <= vol <= 287:
            basket = 2
        elif 288 <= vol <= 431:
            basket = 3
        elif 432 <= vol <= 719:
            basket = 4
        elif 720 <= vol <= 1007:
            basket = 5
        elif 1008 <= vol <= 1061:
            basket = 6
        elif 1062 <= vol <= 1115:
            basket = 7
        elif 1116 <= vol <= 1169:
            basket = 8
        elif 1170 <= vol <= 1313:
            basket = 9
        elif 1314 <= vol <= 1601:
            basket = 10
        elif 1602 <= vol <= 1655:
            basket = 11
        elif 1656 <= vol <= 1919:
            basket = 12
        elif 1920 <= vol <= 2045:
            basket = 13
        elif 2046 <= vol <= 2189:
            basket = 14
        elif 2190 <= vol <= 2405:
            basket = 15
        elif 2406 <= vol <= 2621:
            basket = 16
        elif 2622 <= vol <= 2837:
            basket = 17
        else:
            basket = 18
        b_str = f"0{basket}" if basket < 10 else f"{basket}"
        return f"https://basket-{b_str}.wbbasket.ru/vol{vol}/part{part}/{nm}/images/big/1.webp"
    except Exception:
        return None


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
                    price_raw = (
                        bh_data.get("price")
                        or (bh_data.get("price_info") or {}).get("price")
                        or bh_data.get("card_price")
                        or bh_data.get("final_price")
                    )
                    price = _format_price(price_raw)
                    brand = bh_data.get("brand") or bh_data.get("brand_name")
                    rating = bh_data.get("rating") or bh_data.get("review_rating")
                    reviews_count = bh_data.get("reviews_count") or bh_data.get("feedbacks_count")
                    desc = bh_data.get("description") or bh_data.get("short_description") or ""

                    image_url = _extract_image_from_dict(bh_data)
                    specs = _extract_specs_from_dict(bh_data)
                    if sku and "Артикул" not in specs:
                        specs["Артикул / SKU"] = sku

                    details = []
                    if price:
                        details.append(f"Цена: {price}")
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
                        image_url=image_url,
                        price=price,
                        specs=specs or None,
                    )
            except Exception as e:
                logger.warning("Error processing BHAPI Ozon product: %s", e)

        # 2. Fallback to OpenGraph / HTML / JSON-LD extraction
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
                    price = _format_price(price_val)

                    # Extract image
                    image_url = None
                    ld_image = json_ld.get("image")
                    if isinstance(ld_image, str) and ld_image.startswith("http"):
                        image_url = ld_image
                    elif isinstance(ld_image, list) and ld_image:
                        image_url = ld_image[0] if isinstance(ld_image[0], str) else None
                    if not image_url:
                        og_img = soup.find("meta", property="og:image") or soup.find("meta", attrs={"name": "og:image"})
                        if og_img and og_img.get("content") and og_img["content"].startswith("http"):
                            image_url = og_img["content"]

                    specs = _extract_specs_from_dict(json_ld)
                    if sku and "Артикул" not in specs:
                        specs["Артикул / SKU"] = sku

                    details = []
                    if price:
                        details.append(f"Цена: {price}")
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
                        image_url=image_url,
                        price=price,
                        specs=specs or None,
                    )
        except Exception as e:
            logger.warning("Fallback Ozon extractor failed: %s", e)

        return ExtractedMetadata(
            title=fallback_title,
            description=fallback_desc,
            site_type=SiteType.ozon,
            image_url=None,
            price=None,
            specs={"Артикул": sku} if sku else None,
        )


class WildberriesExtractor(BaseExtractor):
    def __init__(self, client: Optional[BhapiClient] = None):
        self.client = client or bhapi_client

    async def extract(self, url: str) -> ExtractedMetadata:
        article_match = re.search(r'/catalog/(\d+)', url) or re.search(r'nm=(\d+)', url) or re.search(r'/product/(\d+)', url)
        article = article_match.group(1) if article_match else None

        fallback_title = f"Wildberries Товар {f'(арт. {article})' if article else ''}".strip()
        fallback_desc = "Товар на маркетплейсе Wildberries."
        fallback_image = _get_wb_cdn_image(article) if article else None

        # 1. Try BHAPI if configured
        if self.client.is_configured():
            try:
                bh_data = await self.client.get_wb_product(url)
                if bh_data:
                    title = bh_data.get("imt_name") or bh_data.get("name") or bh_data.get("title") or bh_data.get("goods_name")
                    price_raw = bh_data.get("price") or bh_data.get("sale_price_u") or bh_data.get("final_price")
                    price = _format_price(price_raw)
                    brand = bh_data.get("brand") or bh_data.get("brand_name")
                    rating = bh_data.get("review_rating") or bh_data.get("rating")
                    feedbacks = bh_data.get("feedbacks_count") or bh_data.get("reviews_count")
                    desc = bh_data.get("description") or ""

                    image_url = _extract_image_from_dict(bh_data) or fallback_image
                    specs = _extract_specs_from_dict(bh_data)
                    if article and "Артикул" not in specs:
                        specs["Артикул"] = article

                    details = []
                    if price:
                        details.append(f"Цена: {price}")
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
                        image_url=image_url,
                        price=price,
                        specs=specs or None,
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
                            price_val = None
                            if sizes and isinstance(sizes, list):
                                price_val = (sizes[0].get("price") or {}).get("total")
                            if not price_val:
                                price_val = prod.get("salePriceU") or prod.get("priceU")

                            price = _format_price(price_val // 100 if price_val and price_val > 100000 else price_val)
                            rating = prod.get("rating") or prod.get("reviewRating")
                            feedbacks = prod.get("feedbacks")

                            title = f"{name} {f'– {brand}' if brand else ''}".strip()
                            details = []
                            if price:
                                details.append(f"Цена: {price}")
                            if brand:
                                details.append(f"Бренд: {brand}")
                            if rating:
                                r_str = f"★ {rating}"
                                if feedbacks:
                                    r_str += f" ({feedbacks} отзывов)"
                                details.append(r_str)

                            final_desc = f"Wildberries (арт. {article}) | " + " | ".join(details)
                            specs = {"Артикул": article}
                            if brand:
                                specs["Бренд"] = brand
                            if rating:
                                specs["Рейтинг"] = str(rating)

                            return ExtractedMetadata(
                                title=title or fallback_title,
                                description=final_desc,
                                site_type=SiteType.wildberries,
                                image_url=fallback_image,
                                price=price,
                                specs=specs,
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
                    og_img = soup.find("meta", property="og:image") or soup.find("meta", attrs={"name": "og:image"})

                    title = og_title.get("content").strip() if og_title and og_title.get("content") else None
                    desc = og_desc.get("content").strip() if og_desc and og_desc.get("content") else None
                    image_url = og_img.get("content").strip() if og_img and og_img.get("content") else fallback_image

                    return ExtractedMetadata(
                        title=title or fallback_title,
                        description=desc or fallback_desc,
                        site_type=SiteType.wildberries,
                        image_url=image_url,
                        price=None,
                        specs={"Артикул": article} if article else None,
                    )
        except Exception:
            pass

        return ExtractedMetadata(
            title=fallback_title,
            description=fallback_desc,
            site_type=SiteType.wildberries,
            image_url=fallback_image,
            price=None,
            specs={"Артикул": article} if article else None,
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
                    price_raw = bh_data.get("price") or bh_data.get("final_price") or bh_data.get("sale_price")
                    price = _format_price(price_raw)
                    store = bh_data.get("store_name") or bh_data.get("seller")
                    rating = bh_data.get("rating")
                    orders = bh_data.get("orders") or bh_data.get("sales_count")
                    desc = bh_data.get("description") or ""

                    image_url = _extract_image_from_dict(bh_data)
                    specs = _extract_specs_from_dict(bh_data)
                    if item_id and "Item ID" not in specs:
                        specs["ID товара"] = item_id

                    details = []
                    if price:
                        details.append(f"Цена: {price}")
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
                        image_url=image_url,
                        price=price,
                        specs=specs or None,
                    )
            except Exception as e:
                logger.warning("Error processing BHAPI AliExpress product: %s", e)

        # 2. Fallback to OpenGraph / HTML / JSON-LD scraping
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
                    if not price_val:
                        og_p = soup.find("meta", property="og:price:amount") or soup.find("meta", property="product:price:amount")
                        if og_p and og_p.get("content"):
                            price_val = og_p["content"]
                    price = _format_price(price_val)

                    image_url = None
                    ld_img = json_ld.get("image")
                    if isinstance(ld_img, str) and ld_img.startswith("http"):
                        image_url = ld_img
                    elif isinstance(ld_img, list) and ld_img:
                        image_url = ld_img[0] if isinstance(ld_img[0], str) else None
                    if not image_url:
                        og_img = soup.find("meta", property="og:image") or soup.find("meta", attrs={"name": "og:image"})
                        if og_img and og_img.get("content") and og_img["content"].startswith("http"):
                            image_url = og_img["content"]

                    specs = _extract_specs_from_dict(json_ld)
                    if item_id and "ID товара" not in specs:
                        specs["ID товара"] = item_id

                    details = []
                    if price:
                        details.append(f"Цена: {price}")
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
                        image_url=image_url,
                        price=price,
                        specs=specs or None,
                    )
        except Exception as e:
            logger.warning("Fallback AliExpress extractor failed: %s", e)

        return ExtractedMetadata(
            title=fallback_title,
            description=fallback_desc,
            site_type=SiteType.aliexpress,
            image_url=None,
            price=None,
            specs={"ID товара": item_id} if item_id else None,
        )
