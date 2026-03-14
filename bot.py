"""
Jarvis 3D Print Advisor Bot — Railway edition
Авто-отчёты через встроенный JobQueue (APScheduler не нужен)
"""

import logging
from datetime import datetime
from telegram import Update, BotCommand
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes,
)
from telegram.constants import ParseMode

from agent import JarvisAgent
from scraper import MarketScraper
from config import Config

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

config = Config()
agent  = JarvisAgent(config)
scraper = MarketScraper(config)


# ─── Команды ────────────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🤖 Jarvis — AI-советник по 3D-печати\n\n"
        "Отслеживаю MakerWorld и Etsy, нахожу модели с высоким потенциалом продаж.\n\n"
        "Команды:\n"
        "/analyze — анализ рынка прямо сейчас\n"
        "/top — топ-10 рекомендаций\n"
        "/niche [запрос] — анализ конкретной ниши\n"
        "/schedule — расписание авто-отчётов\n\n"
        "Или просто напиши вопрос!"
    )
    await update.message.reply_text(text)
```



async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("🔍 Запускаю анализ рынка... ~30-60 секунд.")
    try:
        data   = await scraper.fetch_all()
        report = await agent.analyze_market(data)
        await msg.edit_text(report, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        logger.error(f"Analyze error: {e}")
        await msg.edit_text(f"❌ Ошибка: {e}")


async def top_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("📊 Формирую топ рекомендаций...")
    try:
        data   = await scraper.fetch_all()
        report = await agent.get_top_recommendations(data)
        await msg.edit_text(report, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        logger.error(f"Top error: {e}")
        await msg.edit_text(f"❌ Ошибка: {e}")


async def niche_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args) if context.args else ""
    if not query:
        await update.message.reply_text(
            "Укажи нишу. Пример: `/niche organizer kitchen`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    msg = await update.message.reply_text(
        f"🔬 Исследую нишу: *{query}*...", parse_mode=ParseMode.MARKDOWN
    )
    try:
        data   = await scraper.fetch_niche(query)
        report = await agent.analyze_niche(query, data)
        await msg.edit_text(report, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        logger.error(f"Niche error: {e}")
        await msg.edit_text(f"❌ Ошибка: {e}")


async def schedule_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        f"📅 *Авто-отчёты:* каждые {config.AUTO_ANALYZE_HOURS} ч.\n"
        "Отчёты приходят автоматически в этот чат."
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text

    if "history" not in context.chat_data:
        context.chat_data["history"] = []

    context.chat_data["history"].append({"role": "user", "content": user_text})
    if len(context.chat_data["history"]) > 20:
        context.chat_data["history"] = context.chat_data["history"][-20:]

    msg = await update.message.reply_text("🤔 Думаю...")
    try:
        response = await agent.chat(context.chat_data["history"])
        context.chat_data["history"].append({"role": "assistant", "content": response})
        await msg.edit_text(response, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        logger.error(f"Chat error: {e}")
        await msg.edit_text(f"❌ Ошибка: {e}")


# ─── Авто-отчёт (JobQueue — встроен в python-telegram-bot, Railway-совместим) ──

async def auto_report_job(context: ContextTypes.DEFAULT_TYPE):
    chat_id = config.TELEGRAM_CHAT_ID
    if not chat_id:
        logger.warning("TELEGRAM_CHAT_ID не задан — пропускаю авто-отчёт")
        return

    logger.info("Запуск авто-анализа...")
    try:
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"🕐 *Плановый отчёт* — {datetime.now().strftime('%d.%m.%Y %H:%M')}",
            parse_mode=ParseMode.MARKDOWN,
        )
        data   = await scraper.fetch_all()
        report = await agent.analyze_market(data)
        await context.bot.send_message(
            chat_id=chat_id,
            text=report,
            parse_mode=ParseMode.MARKDOWN,
        )
        logger.info("Авто-отчёт отправлен")
    except Exception as e:
        logger.error(f"Auto-report error: {e}")
        try:
            await context.bot.send_message(chat_id=chat_id, text=f"❌ Ошибка авто-отчёта: {e}")
        except Exception:
            pass


# ─── Инициализация ──────────────────────────────────────────────────────────

async def post_init(app: Application):
    await app.bot.set_my_commands([
        BotCommand("start",    "Запустить бота"),
        BotCommand("analyze",  "Полный анализ рынка"),
        BotCommand("top",      "Топ-10 моделей для печати"),
        BotCommand("niche",    "Исследовать нишу"),
        BotCommand("schedule", "Расписание отчётов"),
    ])

    interval = config.AUTO_ANALYZE_HOURS * 3600
    app.job_queue.run_repeating(
        auto_report_job,
        interval=interval,
        first=60,          # первый запуск через 60 сек после старта
        name="auto_report",
    )
    logger.info(f"JobQueue: авто-отчёт каждые {config.AUTO_ANALYZE_HOURS} ч.")


def main():
    if not config.TELEGRAM_TOKEN:
        raise ValueError("TELEGRAM_TOKEN не задан!")
    if not config.ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY не задан!")

    app = (
        Application.builder()
        .token(config.TELEGRAM_TOKEN)
        .post_init(post_init)
        .build()
    )

    app.add_handler(CommandHandler("start",    start))
    app.add_handler(CommandHandler("help",     start))
    app.add_handler(CommandHandler("analyze",  analyze_command))
    app.add_handler(CommandHandler("top",      top_command))
    app.add_handler(CommandHandler("niche",    niche_command))
    app.add_handler(CommandHandler("schedule", schedule_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Jarvis запущен!")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
