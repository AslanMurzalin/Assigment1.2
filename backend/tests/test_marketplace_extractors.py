import pytest
from unittest.mock import AsyncMock, patch
from app.schemas.link import SiteType
from app.services.extractors.dispatcher import metadata_extractor_service
from app.services.extractors.bhapi import BhapiClient
from app.services.extractors.marketplace import (
    OzonExtractor,
    WildberriesExtractor,
    AliExpressExtractor,
    _format_price,
)


def test_url_domain_classification():
    assert metadata_extractor_service.is_ozon_url("https://www.ozon.ru/product/krossovki-nike-123456789/")
    assert metadata_extractor_service.is_ozon_url("https://ozon.by/product/item-123/")
    assert metadata_extractor_service.is_ozon_url("https://ozon.kz/product/item-123/")
    assert not metadata_extractor_service.is_ozon_url("https://example.com/ozon")

    assert metadata_extractor_service.is_wb_url("https://www.wildberries.ru/catalog/12345678/detail.aspx")
    assert metadata_extractor_service.is_wb_url("https://wb.ru/product/12345678")
    assert metadata_extractor_service.is_wb_url("https://wildberries.by/catalog/12345678/detail.aspx")
    assert not metadata_extractor_service.is_wb_url("https://example.com/wb")

    assert metadata_extractor_service.is_aliexpress_url("https://aliexpress.ru/item/10050012345.html")
    assert metadata_extractor_service.is_aliexpress_url("https://www.aliexpress.com/item/10050012345.html")
    assert metadata_extractor_service.is_aliexpress_url("https://ali.express/item/10050012345")
    assert not metadata_extractor_service.is_aliexpress_url("https://example.com/aliexpress")


def test_format_price():
    assert _format_price(1499) == "1 499 ₽"
    assert _format_price("2500") == "2 500 ₽"
    assert _format_price(None) is None


@pytest.mark.anyio
async def test_bhapi_ozon_extractor_success():
    mock_client = BhapiClient(token="test_token")
    mock_ozon_data = {
        "name": "Беспроводные наушники Sony WH-1000XM4",
        "price": 24990,
        "brand": "Sony",
        "rating": 4.9,
        "reviews_count": 842,
        "main_image": "https://cdn1.ozon.ru/multimedia/10000000.jpg",
        "characteristics": {
            "Тип": "Полноразмерные",
            "Шумоподавление": "Активное",
        },
        "description": "Флагманские наушники с шумоподавлением.",
    }

    with patch.object(mock_client, "get_ozon_product", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_ozon_data
        extractor = OzonExtractor(client=mock_client)
        meta = await extractor.extract("https://www.ozon.ru/product/sony-wh-1000xm4-123456789/")

        assert meta.site_type == SiteType.ozon
        assert "Sony WH-1000XM4" in meta.title
        assert meta.price == "24 990 ₽"
        assert meta.image_url == "https://cdn1.ozon.ru/multimedia/10000000.jpg"
        assert meta.specs is not None
        assert meta.specs.get("Brand") == "Sony"
        assert meta.specs.get("Шумоподавление") == "Активное"


@pytest.mark.anyio
async def test_bhapi_wb_extractor_success():
    mock_client = BhapiClient(token="test_token")
    mock_wb_data = {
        "imt_name": "Худи оверсайз с начесом",
        "price": 2890,
        "brand": "Streetwear",
        "review_rating": 4.8,
        "feedbacks_count": 124,
        "photos": ["https://basket-01.wbbasket.ru/vol987/part98765/98765432/images/big/1.webp"],
        "options": [
            {"name": "Состав", "value": "Хлопок 80%, полиэстер 20%"},
            {"name": "Цвет", "value": "Графитовый"},
        ],
        "description": "Теплое и стильное худи.",
    }

    with patch.object(mock_client, "get_wb_product", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_wb_data
        extractor = WildberriesExtractor(client=mock_client)
        meta = await extractor.extract("https://www.wildberries.ru/catalog/98765432/detail.aspx")

        assert meta.site_type == SiteType.wildberries
        assert "Худи оверсайз" in meta.title
        assert meta.price == "2 890 ₽"
        assert meta.image_url == "https://basket-01.wbbasket.ru/vol987/part98765/98765432/images/big/1.webp"
        assert meta.specs is not None
        assert meta.specs.get("Brand") == "Streetwear"
        assert meta.specs.get("Состав") == "Хлопок 80%, полиэстер 20%"


@pytest.mark.anyio
async def test_bhapi_aliexpress_extractor_success():
    mock_client = BhapiClient(token="test_token")
    mock_ali_data = {
        "name": "Механическая клавиатура RGB",
        "price": 3450,
        "store_name": "TechGlobal Store",
        "rating": 4.7,
        "orders": 1500,
        "image": "https://ae01.alicdn.com/kf/S123456789.jpg",
        "properties": {
            "Свитчи": "Gateron Yellow",
            "Подключение": "Type-C / 2.4G",
        },
        "description": "Горячая замена свитчей и настраиваемая подсветка.",
    }

    with patch.object(mock_client, "get_aliexpress_product", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_ali_data
        extractor = AliExpressExtractor(client=mock_client)
        meta = await extractor.extract("https://aliexpress.ru/item/100500987654.html")

        assert meta.site_type == SiteType.aliexpress
        assert "Механическая клавиатура RGB" in meta.title
        assert meta.price == "3 450 ₽"
        assert meta.image_url == "https://ae01.alicdn.com/kf/S123456789.jpg"
        assert meta.specs is not None
        assert meta.specs.get("Свитчи") == "Gateron Yellow"


@pytest.mark.anyio
async def test_marketplace_fallback_without_bhapi_token():
    unconfigured_client = BhapiClient(token="")
    assert not unconfigured_client.is_configured()

    ozon_extractor = OzonExtractor(client=unconfigured_client)
    wb_extractor = WildberriesExtractor(client=unconfigured_client)
    ali_extractor = AliExpressExtractor(client=unconfigured_client)

    ozon_meta = await ozon_extractor.extract("https://www.ozon.ru/product/some-item-123456789/")
    assert ozon_meta.site_type == SiteType.ozon
    assert "Ozon" in ozon_meta.title or "123456789" in ozon_meta.title

    wb_meta = await wb_extractor.extract("https://www.wildberries.ru/catalog/88889999/detail.aspx")
    assert wb_meta.site_type == SiteType.wildberries
    assert "Wildberries" in wb_meta.title or "88889999" in wb_meta.title
    assert wb_meta.image_url is not None  # WB CDN fallback image generated

    ali_meta = await ali_extractor.extract("https://aliexpress.ru/item/100500444555.html")
    assert ali_meta.site_type == SiteType.aliexpress
    assert "AliExpress" in ali_meta.title or "100500444555" in ali_meta.title


def test_api_create_marketplace_links():
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)

    # 1. Register & login
    email = "full_marketplace_tester@example.com"
    pwd = "Password123!"
    client.post("/api/v1/auth/signup", json={"email": email, "password": pwd})
    login_resp = client.post("/api/v1/auth/login", json={"email": email, "password": pwd})
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create Ozon link
    ozon_resp = client.post(
        "/api/v1/links",
        json={"url": "https://www.ozon.ru/product/wireless-mouse-11223344/", "tags": ["shopping", "tech"]},
        headers=headers,
    )
    assert ozon_resp.status_code == 201
    ozon_data = ozon_resp.json()
    assert ozon_data["site_type"] == "ozon"
    assert "title" in ozon_data
    assert "image_url" in ozon_data
    assert "price" in ozon_data
    assert "specs" in ozon_data

    # 3. Create Wildberries link
    wb_resp = client.post(
        "/api/v1/links",
        json={"url": "https://www.wildberries.ru/catalog/77889900/detail.aspx", "tags": ["wb", "clothes"]},
        headers=headers,
    )
    assert wb_resp.status_code == 201
    wb_data = wb_resp.json()
    assert wb_data["site_type"] == "wildberries"
    assert "image_url" in wb_data

    # 4. Create AliExpress link
    ali_resp = client.post(
        "/api/v1/links",
        json={"url": "https://aliexpress.ru/item/100500778899.html", "tags": ["gadgets"]},
        headers=headers,
    )
    assert ali_resp.status_code == 201
    ali_data = ali_resp.json()
    assert ali_data["site_type"] == "aliexpress"
    assert "specs" in ali_data
