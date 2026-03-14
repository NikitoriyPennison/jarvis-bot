"""
Jarvis AI Agent — мозг системы на базе Claude
"""

import anthropic
from typing import List, Dict, Any
from config import Config


SYSTEM_PROMPT = """Ты Jarvis — AI-аналитик рынка 3D-печати. Твоя задача:

1. Анализировать данные с MakerWorld (популярные модели для скачивания/печати) 
   и Etsy (продаваемые 3D-печатные изделия)
2. Находить ПЕРЕСЕЧЕНИЕ: модели которые:
   - Популярны на MakerWorld (много скачиваний, лайков) — значит спрос есть
   - Продаются на Etsy за хорошие деньги — значит монетизируются
   - Не имеют слишком высокой конкуренции
3. Давать конкретные рекомендации что ПЕЧАТАТЬ И ПРОДАВАТЬ

При анализе учитывай:
- Сложность печати (FDM/resin, поддержки, время печати)
- Маржинальность (цена материала vs цена продажи)
- Сезонность и тренды
- Конкуренцию на платформе

Отвечай на русском языке. Будь конкретным, давай числа и ссылки когда есть.
Используй emoji для наглядности. Структурируй ответы с заголовками.
"""


class JarvisAgent:
    def __init__(self, config: Config):
        self.client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        self.model = "claude-sonnet-4-20250514"

    async def chat(self, history: List[Dict]) -> str:
        """Обычный чат с историей"""
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                system=SYSTEM_PROMPT,
                messages=history
            )
            return response.content[0].text
        except Exception as e:
            raise Exception(f"Claude API error: {e}")

    async def analyze_market(self, data: Dict[str, Any]) -> str:
        """Полный анализ рынка"""
        prompt = self._build_analysis_prompt(data)
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=3000,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            raise Exception(f"Claude API error: {e}")

    async def get_top_recommendations(self, data: Dict[str, Any]) -> str:
        """Топ-10 рекомендаций"""
        prompt = f"""На основе этих данных с MakerWorld и Etsy дай ТОП-10 конкретных рекомендаций:
что именно мне напечатать и продать прямо сейчас.

ДАННЫЕ MAKERWORLD:
{self._format_makerworld(data.get('makerworld', []))}

ДАННЫЕ ETSY:
{self._format_etsy(data.get('etsy', []))}

Формат каждой рекомендации:
🥇 [Название модели]
• Почему выгодно: ...
• Примерная цена продажи: $X-Y
• Сложность печати: [Лёгкая/Средняя/Сложная]
• Ссылка: ...
"""
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2500,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            raise Exception(f"Claude API error: {e}")

    async def analyze_niche(self, query: str, data: Dict[str, Any]) -> str:
        """Анализ конкретной ниши"""
        prompt = f"""Проведи детальный анализ ниши: "{query}"

ДАННЫЕ С РЫНКА:
{self._format_makerworld(data.get('makerworld', []))}

ПРОДАЖИ НА ETSY:
{self._format_etsy(data.get('etsy', []))}

Ответь:
1. Оценка ниши (1-10) и почему
2. Топ-5 конкретных товаров для этой ниши
3. Ценовой диапазон
4. Уровень конкуренции
5. Мой вердикт — стоит ли этим заниматься?
"""
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            raise Exception(f"Claude API error: {e}")

    def _build_analysis_prompt(self, data: Dict[str, Any]) -> str:
        mw_text = self._format_makerworld(data.get("makerworld", []))
        etsy_text = self._format_etsy(data.get("etsy", []))

        return f"""🔍 Проведи полный анализ рынка 3D-печати на основе свежих данных.

═══ MAKERWORLD — ПОПУЛЯРНЫЕ МОДЕЛИ ═══
{mw_text}

═══ ETSY — ПРОДАЮЩИЕСЯ ИЗДЕЛИЯ ═══
{etsy_text}

Дай структурированный отчёт:

## 🎯 Главные возможности прямо сейчас
(топ 3-5 конкретных ниш/моделей с обоснованием)

## 📈 Тренды этой недели
(что набирает популярность)

## 💰 Лучшее соотношение усилия/прибыли
(что легко напечатать и дорого продать)

## ⚠️ Что НЕ стоит печатать
(перенасыщенные ниши)

## 🚀 Моя главная рекомендация
(одна конкретная модель/ниша с планом действий)
"""

    def _format_makerworld(self, items: List[Dict]) -> str:
        if not items:
            return "Данные недоступны (сайт заблокировал скрапинг)"
        lines = []
        for i, item in enumerate(items[:20], 1):
            lines.append(
                f"{i}. {item.get('title', 'N/A')} | "
                f"⬇️ {item.get('downloads', 0)} | "
                f"❤️ {item.get('likes', 0)} | "
                f"🔗 {item.get('url', '')}"
            )
        return "\n".join(lines)

    def _format_etsy(self, items: List[Dict]) -> str:
        if not items:
            return "Данные недоступны"
        lines = []
        for i, item in enumerate(items[:20], 1):
            lines.append(
                f"{i}. {item.get('title', 'N/A')} | "
                f"💵 {item.get('price', 'N/A')} | "
                f"⭐ {item.get('reviews', 0)} отзывов | "
                f"🏪 {item.get('shop', 'N/A')}"
            )
        return "\n".join(lines)
