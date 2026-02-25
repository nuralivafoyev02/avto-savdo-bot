from aiogram import Router, F
from aiogram.types import CallbackQuery, Message

from config import ADMIN_IDS
from database.manager import db_manager
from keyboards.inline import admin_panel_keyboard

router = Router()


def _is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


def _deny_text() -> str:
    return "❌ Bu bo‘lim faqat adminlar uchun."


@router.message(F.text == '/admin')
async def admin_panel(message: Message) -> None:
    if not _is_admin(message.from_user.id):
        await message.answer(_deny_text())
        return

    await message.answer(
        "🛠 Admin panel\n\nKerakli bo‘limni tanlang:",
        reply_markup=admin_panel_keyboard(),
    )


@router.callback_query(F.data == 'admin:stats')
async def admin_stats(call: CallbackQuery) -> None:
    if not _is_admin(call.from_user.id):
        await call.answer(_deny_text(), show_alert=True)
        return

    stats = await db_manager.get_stats()
    top_region = stats['top_region'] or '—'

    text = (
        "📊 <b>Bot statistikasi</b>\n\n"
        f"👥 Userlar: <b>{stats['total_users']}</b>\n"
        f"📢 Jami e’lonlar: <b>{stats['total_cars']}</b>\n"
        f"🟢 Aktiv e’lonlar: <b>{stats['active_cars']}</b>\n"
        f"✅ Sotilganlar: <b>{stats['sold_cars']}</b>\n"
        f"🗓 Bugungi e’lonlar: <b>{stats['today_ads']}</b>\n"
        f"📍 Eng faol hudud: <b>{top_region}</b> ({stats['top_region_count']})"
    )

    await call.message.answer(text)
    await call.answer()


@router.callback_query(F.data == 'admin:recent')
async def admin_recent(call: CallbackQuery) -> None:
    if not _is_admin(call.from_user.id):
        await call.answer(_deny_text(), show_alert=True)
        return

    recent = await db_manager.get_recent_cars(limit=5)
    if not recent:
        await call.message.answer("ℹ️ Hali e’lonlar yo‘q.")
        await call.answer()
        return

    lines = ["🕒 <b>Oxirgi 5 ta e’lon</b>", ""]
    for car in recent:
        status = '✅ sotilgan' if car.get('status') == 'sold' else '🟢 aktiv'
        lines.append(
            f"#{car['id']} — {car.get('model')} — {car.get('price')}$ — {status}"
        )

    await call.message.answer("\n".join(lines))
    await call.answer()
