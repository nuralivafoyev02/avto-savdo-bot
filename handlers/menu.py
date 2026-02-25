from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from keyboards.reply import main_menu

router = Router()


@router.message()
async def fallback_menu(message: Message, state: FSMContext) -> None:
    # Agar foydalanuvchi FSM jarayonida bo'lsa, bu handler aralashmaydi.
    # Router tartibi sababli odatda bu joyga faqat noma'lum buyruqlar keladi.
    current_state = await state.get_state()
    if current_state:
        return

    await message.answer(
        '❌ Buyruq tushunilmadi.\n\n'
        'Iltimos, menyudagi tugmalardan birini tanlang:',
        reply_markup=main_menu(),
    )
