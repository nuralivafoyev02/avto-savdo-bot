from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def phone_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='📞 Telefon raqamni yuborish', request_contact=True)],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )



def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='🔍 Mashina qidirish')],
            [KeyboardButton(text='📢 Mashina reklama berish')],
        ],
        resize_keyboard=True,
    )
