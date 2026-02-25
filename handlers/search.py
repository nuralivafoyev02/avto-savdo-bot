import logging

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from database.manager import db_manager
from states.search import SearchCarStates
from utils.formatter import format_car

logger = logging.getLogger(__name__)
router = Router()

CANCEL_TEXTS = {'bekor', '/cancel', 'cancel'}


async def _ensure_registered(message: Message) -> bool:
    user = await db_manager.get_user(str(message.from_user.id))
    if user:
        return True
    await message.answer("❌ Avval /start bosing va telefon raqamingizni yuboring.")
    return False


@router.message(F.text == '🔍 Mashina qidirish')
async def search_start(message: Message, state: FSMContext) -> None:
    if not await _ensure_registered(message):
        return

    await state.clear()
    await state.set_state(SearchCarStates.waiting_for_model)
    await message.answer(
        '🔍 Mashina qidirish\n\n'
        'Qaysi modelni qidiryapsiz?\n'
        '(Masalan: Toyota, Chevrolet, Hyundai)\n\n'
        'Bekor qilish uchun: bekor'
    )


@router.message(SearchCarStates.waiting_for_model, F.text)
async def get_model(message: Message, state: FSMContext) -> None:
    text = message.text.strip()
    if text.lower() in CANCEL_TEXTS:
        await state.clear()
        await message.answer('❌ Qidiruv bekor qilindi.')
        return

    await state.update_data(model=text)
    await state.set_state(SearchCarStates.waiting_for_price_min)
    await message.answer(
        '💰 Minimal narxni kiriting\n'
        '(Masalan: 5000)\n'
        'Yoki SKIP deb yozing.'
    )


@router.message(SearchCarStates.waiting_for_price_min, F.text)
async def get_price_min(message: Message, state: FSMContext) -> None:
    text = message.text.strip()
    if text.lower() in CANCEL_TEXTS:
        await state.clear()
        await message.answer('❌ Qidiruv bekor qilindi.')
        return

    price_min = 0
    if text.upper() != 'SKIP':
        if not text.isdigit():
            await message.answer("❌ Faqat raqam kiriting yoki SKIP deb yozing.")
            return
        price_min = int(text)

    await state.update_data(price_min=price_min)
    await state.set_state(SearchCarStates.waiting_for_price_max)
    await message.answer(
        '💰 Maksimal narxni kiriting\n'
        '(Masalan: 50000)\n'
        'Yoki SKIP deb yozing.'
    )


@router.message(SearchCarStates.waiting_for_price_max, F.text)
async def get_price_max(message: Message, state: FSMContext) -> None:
    text = message.text.strip()
    if text.lower() in CANCEL_TEXTS:
        await state.clear()
        await message.answer('❌ Qidiruv bekor qilindi.')
        return

    price_max = 999_999_999
    if text.upper() != 'SKIP':
        if not text.isdigit():
            await message.answer("❌ Faqat raqam kiriting yoki SKIP deb yozing.")
            return
        price_max = int(text)

    data = await state.get_data()
    model = data.get('model', '')
    price_min = data.get('price_min', 0)
    await state.clear()

    results = await db_manager.search_cars(
        model=model,
        price_min=price_min,
        price_max=price_max,
    )

    max_label = price_max if price_max != 999_999_999 else 'cheksiz'

    if not results:
        await message.answer(
            f"❌ Hech narsa topilmadi.\n\n"
            f"Model: {model}\n"
            f"Narx oralig‘i: {price_min}$ - {max_label}$"
        )
        return

    await message.answer(
        f"✅ {len(results)} ta mashina topildi.\n\n"
        f"Model: {model}\n"
        f"Narx oralig‘i: {price_min}$ - {max_label}$"
    )

    for car in results:
        try:
            photo = car.get('photo')
            caption = format_car(car)
            if photo:
                await message.answer_photo(photo=photo, caption=caption)
            else:
                await message.answer(caption)
        except Exception as e:
            logger.error(f'Search result yuborishda xatolik: {e}', exc_info=True)


@router.message(SearchCarStates.waiting_for_model)
@router.message(SearchCarStates.waiting_for_price_min)
@router.message(SearchCarStates.waiting_for_price_max)
async def invalid_search_input(message: Message) -> None:
    await message.answer('⚠️ Iltimos matn yuboring.')
