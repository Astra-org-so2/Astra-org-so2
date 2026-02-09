"""
Главный файл приложения
"""
import asyncio
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode

from config import settings
from database import db
from bot import router as bot_router
from webapp import create_app

# Настройка логирования
logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def on_startup():
    """Действия при запуске"""
    logger.info("Starting application...")
    
    # Подключаемся к БД
    await db.connect()
    await db.init_db()
    
    logger.info("Database initialized")


async def on_shutdown():
    """Действия при остановке"""
    logger.info("Shutting down...")
    
    # Закрываем БД
    await db.disconnect()
    
    logger.info("Application stopped")


async def start_bot():
    """Запуск Telegram бота"""
    bot = Bot(token=settings.BOT_TOKEN, parse_mode=ParseMode.HTML)
    dp = Dispatcher()
    
    # Регистрируем роутер
    dp.include_router(bot_router)
    
    # Startup/Shutdown
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    logger.info("Bot is starting...")
    
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


async def start_webapp():
    """Запуск Web App сервера"""
    app = create_app()
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(
        runner,
        host=settings.WEBAPP_HOST,
        port=settings.WEBAPP_PORT
    )
    
    await site.start()
    
    logger.info(f"Web App server started at http://{settings.WEBAPP_HOST}:{settings.WEBAPP_PORT}")
    
    # Держим сервер запущенным
    try:
        await asyncio.Event().wait()
    finally:
        await runner.cleanup()


async def main():
    """Главная функция - запуск бота и веб-сервера"""
    await on_startup()
    
    # Запускаем бота и веб-сервер параллельно
    await asyncio.gather(
        start_bot(),
        start_webapp()
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
    finally:
        asyncio.run(on_shutdown())
