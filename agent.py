import google.genai as genai
from typing import List, Dict, Any
from config import Config

SYSTEM_PROMPT = "Ты Jarvis - аналитик рынка 3D-печати. Анализируй MakerWorld и Etsy, давай рекомендации что печатать и продавать. Отвечай на русском."

class JarvisAgent:
    def __init__(self, config: Config):
        self.client = genai.Client(api_key=config.GEMINI_API_KEY)
        self.mdl = "gemini-2.0-flash"

    async def chat(self, history: List[Dict]) -> str:
        try:
            txt = SYSTEM_PROMPT + "\n" + "\n".join([m["role"]+": "+m["content"] for m in history])
            return self.client.models.generate_content(model=self.mdl, contents=txt).text
        except Exception as e:
            raise Exception(f"Gemini error: {e}")

    async def analyze_market(self, data: Dict) -> str:
        try:
            return self.client.models.generate_content(model=self.mdl, contents=self._prompt(data)).text
        except Exception as e:
            raise Exception(f"Gemini error: {e}")

    async def get_top_recommendations(self, data: Dict) -> str:
        try:
            p = "ТОП-10 рекомендаций.\nMAKERWORLD:\n" + self._mw(data) + "\nETSY:\n" + self._etsy(data)
            return self.client.models.generate_content(model=self.mdl, contents=p).text
        except Exception as e:
            raise Exception(f"Gemini error: {e}")

    async def analyze_niche(self, query: str, data: Dict) -> str:
        try:
            p = "Анализ ниши: " + query + "\nMAKERWORLD:\n" + self._mw(data) + "\nETSY:\n" + self._etsy(data) + "\nОценка 1-10, топ-5 товаров, цены, конкуренция, вердикт."
            return self.client.models.generate_content(model=self.mdl, contents=p).text
        except Exception as e:
            raise Exception(f"Gemini error: {e}")

    def _prompt(self, data: Dict) -> str:
        return SYSTEM_PROMPT + "\nMAKERWORLD:\n" + self._mw(data) + "\nETSY:\n" + self._etsy(data) + "\nГлавные возможности, тренды, соотношение усилия/прибыли, что не стоит печатать, главная рекомендация."

    def _mw(self, data: Dict) -> str:
        items = data.get("makerworld", [])
        if not items:
            return "Нет данных"
        return "\n".join([str(i) + ". " + str(x.get("title", "N/A")) + " | " + str(x.get("downloads", 0)) for i, x in enumerate(items[:20], 1)])

    def _etsy(self, data: Dict) -> str:
        items = data.get("etsy", [])
        if not items:
            return "Нет данных"
        return "\n".join([str(i) + ". " + str(x.get("title", "N/A")) + " | " + str(x.get("price", "N/A")) for i, x in enumerate(items[:20], 1)])