import httpx
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from app.schemas.link import SiteType
from app.services.extractors.base import BaseExtractor, ExtractedMetadata

class GenericExtractor(BaseExtractor):
    async def extract(self, url: str) -> ExtractedMetadata:
        parsed = urlparse(url)
        domain = parsed.netloc.replace("www.", "")
        fallback_title = f"{domain} {parsed.path.strip('/').replace('/', ' - ')}".strip() or domain
        fallback_desc = f"Saved webpage from {domain}."

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36 LinkSaver/1.0"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

        try:
            async with httpx.AsyncClient(timeout=4.0, follow_redirects=True) as client:
                resp = await client.get(url, headers=headers)
                if resp.status_code < 400:
                    soup = BeautifulSoup(resp.text, "html.parser")

                    # Title priority: og:title -> <title>
                    og_title = soup.find("meta", property="og:title") or soup.find("meta", attrs={"name": "og:title"})
                    page_title = soup.find("title")

                    title = None
                    if og_title and og_title.get("content"):
                        title = og_title["content"].strip()
                    elif page_title and page_title.string:
                        title = page_title.string.strip()

                    # Description priority: og:description -> meta description
                    og_desc = soup.find("meta", property="og:description") or soup.find("meta", attrs={"name": "og:description"})
                    meta_desc = soup.find("meta", attrs={"name": "description"})

                    description = None
                    if og_desc and og_desc.get("content"):
                        description = og_desc["content"].strip()
                    elif meta_desc and meta_desc.get("content"):
                        description = meta_desc["content"].strip()

                    return ExtractedMetadata(
                        title=title or fallback_title,
                        description=description or fallback_desc,
                        site_type=SiteType.generic,
                    )
        except Exception:
            pass

        return ExtractedMetadata(
            title=fallback_title,
            description=fallback_desc,
            site_type=SiteType.generic,
        )
