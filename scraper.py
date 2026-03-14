"""
Scraper для MakerWorld и Etsy
Использует httpx + BeautifulSoup для парсинга
"""

import asyncio
import httpx
import json
import logging
from typing import Dict, List, Any
from bs4 import BeautifulSoup
from config import Config

logger = logging.getLogger(__name__)


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


class MarketScraper:
    def __init__(self, config: Config):
        self.config = config
        self.timeout = httpx.Timeout(30.0)

    async def fetch_all(self) -> Dict[str, List[Dict]]:
        """Параллельно собираем данные с обоих сайтов"""
        logger.info("Запуск параллельного сбора данных...")
        mw_task = asyncio.create_task(self._fetch_makerworld())
        etsy_task = asyncio.create_task(self._fetch_etsy_3dprint())

        mw_data, etsy_data = await asyncio.gather(mw_task, etsy_task, return_exceptions=True)

        if isinstance(mw_data, Exception):
            logger.error(f"MakerWorld error: {mw_data}")
            mw_data = []
        if isinstance(etsy_data, Exception):
            logger.error(f"Etsy error: {etsy_data}")
            etsy_data = []

        logger.info(f"Собрано: MakerWorld={len(mw_data)}, Etsy={len(etsy_data)}")
        return {"makerworld": mw_data, "etsy": etsy_data}

    async def fetch_niche(self, query: str) -> Dict[str, List[Dict]]:
        """Ищем данные по конкретной нише"""
        mw_task = asyncio.create_task(self._search_makerworld(query))
        etsy_task = asyncio.create_task(self._search_etsy(query))

        mw_data, etsy_data = await asyncio.gather(mw_task, etsy_task, return_exceptions=True)

        if isinstance(mw_data, Exception):
            logger.error(f"MakerWorld search error: {mw_data}")
            mw_data = []
        if isinstance(etsy_data, Exception):
            logger.error(f"Etsy search error: {etsy_data}")
            etsy_data = []

        return {"makerworld": mw_data, "etsy": etsy_data}

    # ─── MakerWorld ──────────────────────────────────────────────────────────

    async def _fetch_makerworld(self) -> List[Dict]:
        """Топ моделей с MakerWorld через их API"""
        results = []

        # MakerWorld имеет публичный API
        endpoints = [
            ("https://makerworld.com/api/v1/design-service/designs"
             "?limit=20&offset=0&sortBy=downloadCount&locale=en"),
            ("https://makerworld.com/api/v1/design-service/designs"
             "?limit=20&offset=0&sortBy=likeCount&locale=en"),
        ]

        async with httpx.AsyncClient(headers=HEADERS, timeout=self.timeout) as client:
            for url in endpoints:
                try:
                    resp = await client.get(url)
                    if resp.status_code == 200:
                        data = resp.json()
                        items = data.get("hits", data.get("data", []))
                        for item in items:
                            results.append(self._parse_mw_item(item))
                    await asyncio.sleep(1)
                except Exception as e:
                    logger.warning(f"MakerWorld API failed: {e}, пробую скрапинг...")
                    scraped = await self._scrape_makerworld_html(client)
                    results.extend(scraped)
                    break

        # Дедупликация по url
        seen = set()
        unique = []
        for r in results:
            if r["url"] not in seen:
                seen.add(r["url"])
                unique.append(r)
        return unique[:25]

    def _parse_mw_item(self, item: Dict) -> Dict:
        design_id = item.get("id", "")
        return {
            "title": item.get("title", item.get("name", "Unknown")),
            "downloads": item.get("downloadCount", item.get("download_count", 0)),
            "likes": item.get("likeCount", item.get("like_count", 0)),
            "category": item.get("categoryName", item.get("category", "")),
            "author": item.get("designerName", item.get("author", "")),
            "url": f"https://makerworld.com/en/models/{design_id}" if design_id else "",
            "source": "makerworld",
        }

    async def _scrape_makerworld_html(self, client: httpx.AsyncClient) -> List[Dict]:
        """Запасной вариант — скрапинг HTML MakerWorld"""
        results = []
        try:
            url = "https://makerworld.com/en?tab=models&sortBy=downloadCount"
            resp = await client.get(url)
            soup = BeautifulSoup(resp.text, "html.parser")

            # Ищем JSON данные встроенные в страницу (Next.js / React SSR)
            scripts = soup.find_all("script", {"id": "__NEXT_DATA__"})
            for script in scripts:
                try:
                    data = json.loads(script.string)
                    # Обходим вложенные данные Next.js
                    props = data.get("props", {}).get("pageProps", {})
                    models = props.get("models", props.get("designs", []))
                    for m in models[:15]:
                        results.append({
                            "title": m.get("title", "Unknown"),
                            "downloads": m.get("downloadCount", 0),
                            "likes": m.get("likeCount", 0),
                            "url": f"https://makerworld.com/en/models/{m.get('id', '')}",
                            "source": "makerworld-html"
                        })
                    if results:
                        break
                except Exception:
                    continue

            # Если NEXT_DATA не сработал — парсим DOM
            if not results:
                cards = soup.select(".model-card, [class*='ModelCard'], [class*='model-item']")
                for card in cards[:15]:
                    title_el = card.select_one("h3, h2, [class*='title']")
                    link_el = card.select_one("a[href]")
                    results.append({
                        "title": title_el.get_text(strip=True) if title_el else "Unknown",
                        "downloads": 0,
                        "likes": 0,
                        "url": "https://makerworld.com" + link_el["href"] if link_el else "",
                        "source": "makerworld-dom"
                    })

        except Exception as e:
            logger.error(f"HTML scrape MakerWorld failed: {e}")

        return results

    async def _search_makerworld(self, query: str) -> List[Dict]:
        """Поиск по MakerWorld"""
        results = []
        try:
            url = (
                f"https://makerworld.com/api/v1/design-service/designs"
                f"?limit=20&offset=0&keyword={query}&locale=en"
            )
            async with httpx.AsyncClient(headers=HEADERS, timeout=self.timeout) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    items = data.get("hits", data.get("data", []))
                    results = [self._parse_mw_item(i) for i in items]
        except Exception as e:
            logger.error(f"MakerWorld search error: {e}")
        return results

    # ─── Etsy ─────────────────────────────────────────────────────────────────

    async def _fetch_etsy_3dprint(self) -> List[Dict]:
        """Ищем продаваемые 3D-печатные товары на Etsy"""
        all_results = []
        queries = [
            "3d printed",
            "3d print figurine",
            "3d printed organizer",
            "3d printed jewelry",
            "3d printed home decor",
        ]

        async with httpx.AsyncClient(headers=HEADERS, timeout=self.timeout) as client:
            for query in queries[:3]:  # ограничиваем чтобы не забанили
                try:
                    items = await self._search_etsy(query, client)
                    all_results.extend(items)
                    await asyncio.sleep(2)  # вежливая пауза
                except Exception as e:
                    logger.warning(f"Etsy query '{query}' failed: {e}")

        # Сортируем по количеству отзывов (≈ продажи)
        all_results.sort(key=lambda x: x.get("reviews", 0), reverse=True)

        # Дедупликация
        seen = set()
        unique = []
        for r in all_results:
            key = r.get("title", "")[:50]
            if key not in seen:
                seen.add(key)
                unique.append(r)

        return unique[:25]

    async def _search_etsy(self, query: str, client: httpx.AsyncClient = None) -> List[Dict]:
        """Поиск на Etsy"""
        results = []
        close_client = False

        if client is None:
            client = httpx.AsyncClient(headers=HEADERS, timeout=self.timeout)
            close_client = True

        try:
            url = f"https://www.etsy.com/search?q={query.replace(' ', '+')}&explicit=1&order=most_relevant"
            resp = await client.get(url)

            if resp.status_code != 200:
                logger.warning(f"Etsy returned {resp.status_code} for query: {query}")
                return results

            soup = BeautifulSoup(resp.text, "html.parser")

            # Ищем встроенный JSON (Etsy использует SSR с данными в script-тегах)
            for script in soup.find_all("script", type="application/json"):
                try:
                    data = json.loads(script.string or "")
                    listings = self._extract_etsy_listings(data)
                    if listings:
                        results.extend(listings)
                        break
                except Exception:
                    continue

            # Запасной парсинг DOM
            if not results:
                results = self._parse_etsy_dom(soup)

        except Exception as e:
            logger.error(f"Etsy scrape error for '{query}': {e}")
        finally:
            if close_client:
                await client.aclose()

        return results

    def _extract_etsy_listings(self, data: Any) -> List[Dict]:
        """Рекурсивно ищем листинги в JSON Etsy"""
        results = []
        if isinstance(data, list):
            for item in data:
                results.extend(self._extract_etsy_listings(item))
        elif isinstance(data, dict):
            # Типичные ключи Etsy-листингов
            if "listing_id" in data or "listingId" in data:
                price = data.get("price", {})
                price_str = (
                    f"${price.get('amount', price.get('currency_formatted_value', 'N/A'))}"
                    if isinstance(price, dict) else str(price)
                )
                results.append({
                    "title": data.get("title", data.get("listingTitle", "Unknown")),
                    "price": price_str,
                    "reviews": data.get("num_favorers", data.get("reviews_count", 0)),
                    "shop": data.get("shop_name", data.get("shopName", "")),
                    "url": data.get("url", data.get("listing_url", "")),
                    "source": "etsy"
                })
            else:
                for v in data.values():
                    results.extend(self._extract_etsy_listings(v))
        return results[:20]

    def _parse_etsy_dom(self, soup: BeautifulSoup) -> List[Dict]:
        """Парсим DOM Etsy как запасной вариант"""
        results = []
        # Etsy меняет классы, используем универсальные селекторы
        cards = soup.select(
            "[data-listing-id], "
            ".v2-listing-card, "
            "[class*='listing-link']"
        )
        for card in cards[:15]:
            title_el = card.select_one("h3, h2, [class*='title']")
            price_el = card.select_one("[class*='price'], .currency-value")
            link_el = card.select_one("a[href*='/listing/']")

            title = title_el.get_text(strip=True) if title_el else "Unknown"
            price = price_el.get_text(strip=True) if price_el else "N/A"
            url = link_el["href"] if link_el else ""
            if url and not url.startswith("http"):
                url = "https://www.etsy.com" + url

            results.append({
                "title": title[:100],
                "price": price,
                "reviews": 0,
                "shop": "",
                "url": url,
                "source": "etsy-dom"
            })

        return results
