from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    WebAppInfo,
)
from aiogram.fsm.context import FSMContext

from states.add_car import AddCarStates
from keyboards.inline import confirm_keyboard, buy_button
from database.manager import db_manager
from utils.formatter import format_car
from config import CHANNEL_ID
from loader import bot

router = Router()

MINI_APP_URL = "https://avto-miniapp-starter.vercel.app"


def add_entry_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🚘 Mini App orqali joylash",
                    web_app=WebAppInfo(url=MINI_APP_URL),
                )
            ],
            [
                InlineKeyboardButton(
                    text="🤖 Bot ichida davom etish",
                    callback_data="add_car_bot",
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Bekor qilish",
                    callback_data="add_car_entry_cancel",
                )
            ],
        ]
    )


def mini_app_after_post_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📂 Mening e’lonlarim (Mini App)",
                    web_app=WebAppInfo(url=MINI_APP_URL),
                )
            ]
        ]
    )


@router.message(F.text == "📢 Mashina reklama berish")
async def add_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "📢 E’lon joylash uchun usulni tanlang:\n\n"
        "1) 🚘 Mini App — tezroq, qulayroq, chiroyli interfeys\n"
        "2) 🤖 Bot ichida — eski usulda bosqichma-bosqich",
        reply_markup=add_entry_keyboard(),
    )


@router.callback_query(F.data == "add_car_bot")
async def add_start_in_bot(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(AddCarStates.photos)

    await call.message.answer(
        "📸 Mashina rasmini yuboring\n\n"
        "Ushbu jarayonda quyidagi ma'lumotlarni kiritish kerak bo'ladi:\n"
        "• Mashina modeli\n"
        "• Narxi\n"
        "• Holati (Yangi/Ishlatilgan)\n"
        "• Uzatma (Mexanika/Avtomat)\n"
        "• Rangi\n"
        "• Probeg (km)\n"
        "• Viloyat"
    )
    await call.answer()


@router.callback_query(F.data == "add_car_entry_cancel")
async def add_entry_cancel(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.answer("❌ E’lon berish bekor qilindi!")
    await call.answer()


@router.message(AddCarStates.photos, F.photo)
async def get_photo(message: Message, state: FSMContext):
    await state.update_data(photo=message.photo[-1].file_id)
    await state.set_state(AddCarStates.model)
    await message.answer("🚗 Mashina modeli? (Masalan: Toyota Camry)")


@router.message(AddCarStates.model, F.text)
async def get_model(message: Message, state: FSMContext):
    await state.update_data(model=message.text)
    await state.set_state(AddCarStates.price)
    await message.answer("💰 Narxi nechada? (Faqat raqam, masalan: 15000)")


@router.message(AddCarStates.price, F.text)
async def get_price(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ Iltimos faqat raqam kiriting! (Masalan: 15000)")
        return

    await state.update_data(price=int(message.text))
    await state.set_state(AddCarStates.condition)
    await message.answer("⚙️ Holati?\n1️⃣ Yangi\n2️⃣ Ishlatilgan\n\nJavobni yuboring")


@router.message(AddCarStates.condition, F.text)
async def get_condition(message: Message, state: FSMContext):
    await state.update_data(condition=message.text)
    await state.set_state(AddCarStates.transmission)
    await message.answer("🔧 Uzatma turini tanlang:\n\n1️⃣ Mexanika\n2️⃣ Avtomat\n\nJavobni yuboring")


@router.message(AddCarStates.transmission, F.text)
async def get_transmission(message: Message, state: FSMContext):
    await state.update_data(transmission=message.text)
    await state.set_state(AddCarStates.color)
    await message.answer("🎨 Mashina rangi nima? (Masalan: Qora, Oq, Qizil)")


@router.message(AddCarStates.color, F.text)
async def get_color(message: Message, state: FSMContext):
    await state.update_data(color=message.text)
    await state.set_state(AddCarStates.mileage)
    await message.answer("📏 Probeg nechada (km)? (Masalan: 125000)")


@router.message(AddCarStates.mileage, F.text)
async def get_mileage(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ Iltimos faqat raqam kiriting! (Masalan: 12500)")
        return

    await state.update_data(mileage=int(message.text))
    await state.set_state(AddCarStates.region)
    await message.answer("📍 Qaysi viloyatda?\n\nToshkent, Samarqand, Buxoro va boshqalar")


@router.message(AddCarStates.region, F.text)
async def get_region(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    user = await db_manager.get_user(user_id)

    if not user:
        await message.answer("❌ Xatolik! Iltimos /start buyrug'ini bosing")
        await state.clear()
        return

    await state.update_data(
        region=message.text,
        user_id=user_id,
        phone=user["phone"],
        username=user["username"],
    )

    data = await state.get_data()
    await message.answer_photo(
        photo=data["photo"],
        caption=format_car(data),
        parse_mode="HTML",
        reply_markup=confirm_keyboard(),
    )


@router.callback_query(F.data == "confirm_send")
async def confirm_send(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    await db_manager.add_car(data)

    channel_reply_markup = buy_button(data["username"]) if data.get("username") else None

    # Keyinchalik mini app admin paneldan tahrirlash uchun:
    # shu joyda send_photo natijasidagi message_id ni saqlab qo'yish mumkin.
    sent = await bot.send_photo(
        chat_id=CHANNEL_ID,
        photo=data["photo"],
        caption=format_car(data),
        parse_mode="HTML",
        reply_markup=channel_reply_markup,
    )

    # Agar keyin channel_message_id qo'shmoqchi bo'lsang:
    # sent.message_id shu yerda tayyor turadi
    _ = sent.message_id

    await call.message.answer(
        "✅ E’lon kanalga yuborildi!\n\n"
        "Mini App orqali e’lonlaringizni boshqarishingiz ham mumkin.",
        reply_markup=mini_app_after_post_keyboard(),
    )
    await call.answer()
    await state.clear()


@router.callback_query(F.data == "cancel")
async def cancel_add(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.answer("❌ Jarayon bekor qilindi!")
    await call.answer()


# Generic error handlers for wrong types
@router.message(AddCarStates.photos)
async def invalid_photo(message: Message):
    await message.answer("⚠️ Iltimos mashina RASMINI yuboring!")


@router.message(AddCarStates.model)
@router.message(AddCarStates.condition)
@router.message(AddCarStates.transmission)
@router.message(AddCarStates.color)
@router.message(AddCarStates.region)
async def invalid_text(message: Message):
    await message.answer("⚠️ Iltimos MATN ko'rinishida yuboring!")


@router.message(AddCarStates.price)
@router.message(AddCarStates.mileage)
async def invalid_number(message: Message):
    await message.answer("⚠️ Iltimos RAQAM ko'rinishida yuboring!")