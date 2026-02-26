from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    WebAppInfo,
)

from keyboards.reply import phone_keyboard, main_menu
from database.manager import db_manager

router = Router()

MINI_APP_URL = "https://avto-miniapp-starter.vercel.app"

def mini_app_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🚘 Mini Appni ochish",
                    web_app=WebAppInfo(url=MINI_APP_URL),
                )
            ]
        ]
    )


@router.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "🚗 Avto botga xush kelibsiz!\n\n"
        "🔍 Mashina qidirish\n"
        "📢 Mashina reklama berish\n\n"
        "Davom etish uchun telefon raqamingizni yuboring 👇",
        reply_markup=phone_keyboard(),
    )

    await message.answer(
        "Yoki to‘g‘ridan-to‘g‘ri mini app orqali ishlashingiz mumkin 👇",
        reply_markup=mini_app_keyboard(),
    )


@router.message(lambda m: m.contact)
async def save_contact(message: Message):
    await db_manager.add_user(
        user_id=str(message.from_user.id),
        phone=message.contact.phone_number,
        username=message.from_user.username,
    )

    await message.answer(
        "✅ Rahmat! Endi foydalanishingiz mumkin.",
        reply_markup=main_menu(),
    )

    await message.answer(
        "🚘 E’lonlarni qulay ko‘rish, qidirish va joylash uchun mini appni ham ishlatishingiz mumkin:",
        reply_markup=mini_app_keyboard(),
    )