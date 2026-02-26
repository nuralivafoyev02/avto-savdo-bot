from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='✅ Kanalga yuborish', callback_data='confirm_send')],
            [InlineKeyboardButton(text='❌ Bekor qilish', callback_data='cancel')],
        ]
    )


def post_keyboard(
    car_id: int,
    owner_user_id: str,
    username: str | None,
    caption_message_id: int = 0,
) -> InlineKeyboardMarkup:
    buttons: list[list[InlineKeyboardButton]] = []

    if username:
        buttons.append(
            [InlineKeyboardButton(text='💬 Sotuvchiga yozish', url=f'https://t.me/{username}')]
        )

    buttons.append(
        [
            InlineKeyboardButton(
                text='✅ Sotildi',
                callback_data=f'sold:{car_id}:{owner_user_id}:{caption_message_id}',
            )
        ]
    )

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_panel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='📊 Statistika', callback_data='admin:stats')],
            [InlineKeyboardButton(text='🕒 Oxirgi 5 e’lon', callback_data='admin:recent')],
        ]
    )


def buy_button(username: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='💬 Sotuvchiga yozish', url=f'https://t.me/{username}')]
        ]
    )