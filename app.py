import asyncio
import logging
import sys

from aiogram.types import MenuButtonWebApp, WebAppInfo

from loader import dp, bot
from database.manager import db_manager
from handlers import start, menu, add_car, search

MINI_APP_URL = "https://YOUR-MINIAPP-DOMAIN.vercel.app"

# Logging sozlamalari
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(__name__)


async def set_mini_app_menu_button() -> None:
    await bot.set_chat_menu_button(
        menu_button=MenuButtonWebApp(
            text="🚘 Mini App",
            web_app=WebAppInfo(url=MINI_APP_URL),
        )
    )


async def main():
    try:
        logger.info("Bot initialization starting...")

        # Initialize Database
        await db_manager.initialize()
        logger.info("✅ Database initialized")

        # Mini App menu button
        try:
            await set_mini_app_menu_button()
            logger.info("✅ Mini App menu button set")
        except Exception as e:
            logger.warning(f"Mini App menu button set bo'lmadi: {e}")

        # Routerlar tartibi muhim: fallback menu eng oxirida bo'lsin
        dp.include_router(start.router)
        logger.info("✅ Start handler loaded")

        dp.include_router(add_car.router)
        logger.info("✅ Add car handler loaded")

        dp.include_router(search.router)
        logger.info("✅ Search handler loaded")

        dp.include_router(menu.router)
        logger.info("✅ Menu handler loaded")

        logger.info("🤖 Bot started successfully!")
        print("=" * 50)
        print("🤖 BOT STARTED SUCCESSFULLY!")
        print("=" * 50)

        # Run polling
        await dp.start_polling(bot)

    except Exception as e:
        logger.error(f"❌ CRITICAL ERROR: {e}", exc_info=True)
        print(f"❌ CRITICAL ERROR: {e}")
        raise


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
        print("\n✋ Bot stopped")
    except Exception as e:
        logger.critical(f"Bot crashed: {e}", exc_info=True)
        print(f"\n❌ Bot crashed: {e}")