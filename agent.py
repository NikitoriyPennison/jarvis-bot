import google.generativeai as genai
from typing import List, Dict, Any
from config import Config

SYSTEM_PROMPT = """Ты Jarvis — AI-аналитик рынка 3D-печати. Анализируй данные с MakerWorld и Etsy, находи пересечение популярных и продаваемых моделей, давай конкретные рекомендации что печатать и продавать. Отвечай на русском языке."""

class JarvisAgent:
    def __init__(self, config: Config):
        genai.configure(api_key=config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(model_name="gemini-1.5-flash", system_instruction=SYSTEM_PROMPT)

    async def chat(self, history: List[Dict]) -> str:
        try:
            gemini_history = []
            for msg in history[:-1]:
                role = "user" if msg["role"] == "user" else "model"
                gemini_history.append({"role": role, "parts": [msg["content"]]})
            chat = self.model.start_chat(history=gemini_history)
            response = chat.send_message(history[-1]["content"])
            return response.text
        except Exception as e:
            raise Exception(f"Gemini API error: {e}")

    async def analyze_market(self, data: Dict[str, Any]) -> str:
        try:
            response = self.model.generate_content(self._build_analysis_prompt(data))
            return response.text
        except Exception as e:
            raise Exception(f"Gemini API error: {e}")

    async def get_top_recommendations(self, data: Dict[str, Any]) -> str:
        prompt = f"Дай ТОП-10 рекомендаций что напечатать и продать.\n\nMAKERWORLD:\n{self._format_makerworld(data.get('makerworld', []))}\n\nETSY:\n{self._format_etsy(data.get('etsy', []))}"
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            raise Exception(f"Gemini API error: {e}")

    async def analyze_niche(self, query: str, data: Dict[str, Any]) -> str:
        prompt = f"Проведи анализ ниши: {query}\n\nMAKERWORLD:\n{self._format_makerworld(data.get('makerworld', []))}\n\nETSY:\n{self._format_etsy(data.get('etsy', []))}\n\nДай оценку 1-10, топ-5 товаров, ценовой диапазон, уровень конкуренции, вердикт."
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            raise Exception(f"Gemini API error: {e}")

    def _build_analysis_prompt(self, data: Dict[str, Any]) -> str:
        return f"Проведи полный анализ рынка 3D-печати.\n\nMAKERWORLD:\n{self._format_makerworld(data.get('makerworld', []))}\n\nETSY:\n{self._format_etsy(data.get('etsy', []))}\n\nДай: главные возможности, тренды, лучшее соотношение усилия/прибыли, что не стоит печатать, главную рекомендацию."

    def _format_makerworld(self, items: List[Dict]) -> str:
        if not items:
            return "Данные недоступны"
        return "\n".join([f"{i}. {item.get('title','N/A')} | Скачиваний: {item.get('downloads',0)} | Лайков: {item.get('likes',0)}" for i, item in enumerate(items[:20], 1)])

    def _format_etsy(self, items: List[Dict]) -> str:
        if not items:
            return "Данные недоступны"
        return "\n".join([f"{i}. {item.get('title','N/A')} | Цена: {item.get('price','N/A')} | Отзывов: {item.get('reviews',0)}" for i, item in enumerate(items[:20], 1)])
```
