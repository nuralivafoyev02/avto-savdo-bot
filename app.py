import asyncio
import logging
import sys

from loader import dp, bot
from database.manager import db_manager
from handlers import start, add_car, search, admin, menu

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(__name__)

async def main() -> None:
    try:
        logger.info('Bot initialization starting...')
        await db_manager.initialize()
        logger.info('✅ Database initialized')

        dp.include_router(start.router)
        dp.include_router(add_car.router)
        dp.include_router(search.router)
        dp.include_router(admin.router)
        dp.include_router(menu.router)

        logger.info('🤖 Bot started successfully!')
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f'❌ CRITICAL ERROR: {e}', exc_info=True)
        raise


if __name__ == '__main__':
    asyncio.run(main())
