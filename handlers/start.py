from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message

from keyboards.reply import phone_keyboard, main_menu
from database.manager import db_manager

router = Router()


@router.message(CommandStart())
async def start_cmd(message: Message) -> None:
    await message.answer(
        '🚗 Avto botga xush kelibsiz!\n\n'
        'Bot orqali siz:\n'
        '• mashina qidirishingiz\n'
        '• mashina reklama berishingiz mumkin\n\n'
        'Davom etish uchun telefon raqamingizni yuboring 👇',
        reply_markup=phone_keyboard(),
    )


@router.message(F.contact)
async def save_contact(message: Message) -> None:
    if not message.contact:
        return

    await db_manager.add_user(
        user_id=str(message.from_user.id),
        phone=message.contact.phone_number,
        username=message.from_user.username,
    )

    await message.answer(
        '✅ Rahmat! Siz muvaffaqiyatli ro‘yxatdan o‘tdingiz.',
        reply_markup=main_menu(),
    )
