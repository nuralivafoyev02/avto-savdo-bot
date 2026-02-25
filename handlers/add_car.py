import logging

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InputMediaPhoto, Message

from config import ADMIN_IDS, CHANNEL_ID
from database.manager import db_manager
from keyboards.inline import confirm_keyboard, post_keyboard
from loader import bot
from states.add_car import AddCarStates
from utils.formatter import format_car

logger = logging.getLogger(__name__)
router = Router()

CANCEL_TEXTS = {'bekor', '/cancel', 'cancel'}
FINISH_TEXTS = {'tayyor', 'boldi', "bo'ldi", 'done', 'finish'}


async def _ensure_registered(message: Message) -> bool:
    user = await db_manager.get_user(str(message.from_user.id))
    if user:
        return True
    await message.answer("❌ Avval /start bosing va telefon raqamingizni yuboring.")
    return False


async def _notify_admins(text: str) -> None:
    if not ADMIN_IDS:
        return

    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, text)
        except Exception as e:
            logger.warning(f'Admin {admin_id} ga xabar yuborilmadi: {e}')


async def _send_preview(message: Message, data: dict) -> None:
    photos = data.get('photos') or []
    caption = format_car(data)

    if photos:
        media = []
        for index, photo in enumerate(photos[:10]):
            if index == 0:
                media.append(InputMediaPhoto(media=photo, caption=caption))
            else:
                media.append(InputMediaPhoto(media=photo))
        await message.answer_media_group(media=media)
    else:
        await message.answer(caption)

    await message.answer(
        "Yuqorida preview ko‘rindi. Hammasi to‘g‘ri bo‘lsa kanalga yuboring.",
        reply_markup=confirm_keyboard(),
    )


async def _send_channel_post(data: dict, car_id: int) -> int | None:
    photos = [photo for photo in (data.get('photos') or []) if photo][:10]
    caption = format_car(data)
    owner_user_id = str(data['user_id'])
    username = data.get('username')

    # 2+ ta rasm bo'lsa, hammasi bitta album bo'lib ketadi
    if len(photos) > 1:
        media = []
        for index, photo in enumerate(photos):
            if index == 0:
                media.append(InputMediaPhoto(media=photo, caption=caption))
            else:
                media.append(InputMediaPhoto(media=photo))

        album_messages = await bot.send_media_group(
            chat_id=CHANNEL_ID,
            media=media,
        )

        # Albumdagi birinchi xabar (caption turgan xabar) ID sini olamiz
        caption_message_id = album_messages[0].message_id

        # Telegram media_group ga inline tugma qo'shmaydi, shuning uchun
        # alohida action message yuboramiz
        await bot.send_message(
            chat_id=CHANNEL_ID,
            text='👇 Bog‘lanish va holat:',
            reply_markup=post_keyboard(
                car_id=car_id,
                owner_user_id=owner_user_id,
                username=username,
                caption_message_id=caption_message_id,
            ),
        )

        return caption_message_id

    # 1 ta rasm bo'lsa, odatdagidek bitta post
    cover_photo = photos[0] if photos else data.get('photo')

    if cover_photo:
        sent_message = await bot.send_photo(
            chat_id=CHANNEL_ID,
            photo=cover_photo,
            caption=caption,
            reply_markup=post_keyboard(
                car_id=car_id,
                owner_user_id=owner_user_id,
                username=username,
                caption_message_id=0,
            ),
        )
        return sent_message.message_id

    sent_message = await bot.send_message(
        chat_id=CHANNEL_ID,
        text=caption,
        reply_markup=post_keyboard(
            car_id=car_id,
            owner_user_id=owner_user_id,
            username=username,
            caption_message_id=0,
        ),
    )
    return sent_message.message_id

@router.message(F.text == '📢 Mashina reklama berish')
async def add_start(message: Message, state: FSMContext) -> None:
    if not await _ensure_registered(message):
        return

    await state.clear()
    await state.update_data(photos=[])
    await state.set_state(AddCarStates.photos)
    await message.answer(
        '📸 Mashina rasmlarini yuboring (1 tadan 10 tagacha).\n\n'
        'Rasm yuborib bo‘lgach <b>tayyor</b> deb yozing.\n'
        'Bekor qilish uchun: <b>bekor</b>'
    )


@router.message(AddCarStates.photos, F.photo)
async def collect_photos(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    photos = list(data.get('photos', []))

    if len(photos) >= 10:
        await message.answer("⚠️ Maksimum 10 ta rasm qabul qilinadi. Endi 'tayyor' deb yozing.")
        return

    photos.append(message.photo[-1].file_id)
    await state.update_data(
        photos=photos,
        photo=photos[0],
    )

    if len(photos) == 1:
        await message.answer(
            "✅ 1 ta rasm saqlandi. Yana rasm yuboring yoki 'tayyor' deb yozing."
        )
    else:
        await message.answer(
            f"✅ {len(photos)} ta rasm saqlandi. Yana yuboring yoki 'tayyor' deb yozing."
        )


@router.message(AddCarStates.photos, F.text)
async def finish_photos(message: Message, state: FSMContext) -> None:
    text = message.text.strip()
    lowered = text.lower()

    if lowered in CANCEL_TEXTS:
        await state.clear()
        await message.answer('❌ E’lon berish bekor qilindi.')
        return

    if lowered not in FINISH_TEXTS:
        await message.answer("⚠️ Avval rasm yuboring. Tugagach 'tayyor' deb yozing.")
        return

    data = await state.get_data()
    photos = data.get('photos') or []
    if not photos:
        await message.answer("❌ Kamida 1 ta rasm yuboring, keyin 'tayyor' deb yozing.")
        return

    await state.set_state(AddCarStates.model)
    await message.answer('🚗 Mashina modeli? (Masalan: Chevrolet Cobalt)')


@router.message(AddCarStates.model, F.text)
async def get_model(message: Message, state: FSMContext) -> None:
    text = message.text.strip()
    if text.lower() in CANCEL_TEXTS:
        await state.clear()
        await message.answer('❌ E’lon berish bekor qilindi.')
        return

    await state.update_data(model=text)
    await state.set_state(AddCarStates.price)
    await message.answer('💰 Narxi nechada? (Faqat raqam, masalan: 15000)')


@router.message(AddCarStates.price, F.text)
async def get_price(message: Message, state: FSMContext) -> None:
    text = message.text.strip()
    if text.lower() in CANCEL_TEXTS:
        await state.clear()
        await message.answer('❌ E’lon berish bekor qilindi.')
        return

    if not text.isdigit():
        await message.answer('❌ Iltimos faqat raqam kiriting!')
        return

    await state.update_data(price=int(text))
    await state.set_state(AddCarStates.condition)
    await message.answer(
        '⚙️ Holati qanday?\n'
        'Masalan: Yangi yoki Ishlatilgan'
    )


@router.message(AddCarStates.condition, F.text)
async def get_condition(message: Message, state: FSMContext) -> None:
    text = message.text.strip()
    if text.lower() in CANCEL_TEXTS:
        await state.clear()
        await message.answer('❌ E’lon berish bekor qilindi.')
        return

    await state.update_data(condition=text)
    await state.set_state(AddCarStates.transmission)
    await message.answer(
        '🔧 Uzatma turi qanday?\n'
        'Masalan: Mexanika yoki Avtomat'
    )


@router.message(AddCarStates.transmission, F.text)
async def get_transmission(message: Message, state: FSMContext) -> None:
    text = message.text.strip()
    if text.lower() in CANCEL_TEXTS:
        await state.clear()
        await message.answer('❌ E’lon berish bekor qilindi.')
        return

    await state.update_data(transmission=text)
    await state.set_state(AddCarStates.color)
    await message.answer('🎨 Mashina rangi? (Masalan: Oq, Qora, Kumushrang)')


@router.message(AddCarStates.color, F.text)
async def get_color(message: Message, state: FSMContext) -> None:
    text = message.text.strip()
    if text.lower() in CANCEL_TEXTS:
        await state.clear()
        await message.answer('❌ E’lon berish bekor qilindi.')
        return

    await state.update_data(color=text)
    await state.set_state(AddCarStates.mileage)
    await message.answer('📏 Probeg nechada? (km, faqat raqam)')


@router.message(AddCarStates.mileage, F.text)
async def get_mileage(message: Message, state: FSMContext) -> None:
    text = message.text.strip()
    if text.lower() in CANCEL_TEXTS:
        await state.clear()
        await message.answer('❌ E’lon berish bekor qilindi.')
        return

    if not text.isdigit():
        await message.answer('❌ Iltimos probegni faqat raqamda yuboring!')
        return

    await state.update_data(mileage=int(text))
    await state.set_state(AddCarStates.region)
    await message.answer('📍 Qaysi viloyat yoki shaharda?')


@router.message(AddCarStates.region, F.text)
async def get_region(message: Message, state: FSMContext) -> None:
    text = message.text.strip()
    if text.lower() in CANCEL_TEXTS:
        await state.clear()
        await message.answer('❌ E’lon berish bekor qilindi.')
        return

    user_id = str(message.from_user.id)
    user = await db_manager.get_user(user_id)
    if not user:
        await state.clear()
        await message.answer("❌ Foydalanuvchi topilmadi. Avval /start bosing.")
        return

    current_username = (message.from_user.username or '').strip() or user.get('username')

    await state.update_data(
        region=text,
        user_id=user_id,
        phone=user['phone'],
        username=current_username,
    )
    await state.set_state(AddCarStates.confirm)

    data = await state.get_data()
    await _send_preview(message, data)


@router.callback_query(F.data == 'confirm_send')
async def confirm_send(call: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    if not data:
        await call.answer('Ma’lumot topilmadi', show_alert=True)
        return

    car_id = await db_manager.add_car(data)
    channel_message_id = await _send_channel_post(data, car_id)
    await db_manager.set_channel_message_id(car_id, channel_message_id)

    await _notify_admins(
        "🆕 Yangi e’lon qo‘shildi\n"
        f"ID: {car_id}\n"
        f"Model: {data.get('model')}\n"
        f"Narx: {data.get('price')}$\n"
        f"Foydalanuvchi: {data.get('phone')}"
    )

    await state.clear()
    await call.message.answer(f'✅ E’lon kanalga yuborildi! ID: {car_id}')
    await call.answer()


@router.callback_query(F.data == 'cancel')
async def cancel_add(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await call.message.answer('❌ Jarayon bekor qilindi!')
    await call.answer()


@router.callback_query(F.data.startswith('sold:'))
@router.callback_query(F.data.startswith('sold:'))
async def mark_sold(call: CallbackQuery) -> None:
    try:
        parts = call.data.split(':', 3)

        if len(parts) == 4:
            _, car_id_raw, owner_user_id, caption_message_id_raw = parts
            caption_message_id = int(caption_message_id_raw)
        elif len(parts) == 3:
            # eski postlar uchun backward compatibility
            _, car_id_raw, owner_user_id = parts
            caption_message_id = 0
        else:
            raise ValueError

        car_id = int(car_id_raw)
    except (ValueError, AttributeError):
        await call.answer('Noto‘g‘ri so‘rov', show_alert=True)
        return

    if str(call.from_user.id) != owner_user_id and call.from_user.id not in ADMIN_IDS:
        await call.answer('Bu e’lonni faqat egasi yoki admin yopishi mumkin.', show_alert=True)
        return

    updated = await db_manager.mark_car_sold(car_id, owner_user_id)
    if not updated and call.from_user.id in ADMIN_IDS:
        car = await db_manager.get_car(car_id)
        if not car:
            await call.answer('E’lon topilmadi yoki allaqachon sotilgan.', show_alert=True)
            return
        updated = await db_manager.mark_car_sold(car_id, car['user_id'])

    if not updated:
        await call.answer('E’lon topilmadi yoki allaqachon sotilgan.', show_alert=True)
        return

    sold_caption = f"{format_car(updated)}\n\n✅ <b>SOTILDI</b>"

    # Agar bu multi-photo album bo'lsa, caption albumning birinchi xabarida turadi
    if caption_message_id > 0:
        try:
            await bot.edit_message_caption(
                chat_id=CHANNEL_ID,
                message_id=caption_message_id,
                caption=sold_caption,
            )
        except Exception as e:
            logger.warning(f'Album caption edit bo‘lmadi: {e}')

        # Tugmali alohida action message ni yangilaymiz
        try:
            await call.message.edit_text('✅ Sotildi', reply_markup=None)
        except Exception as e:
            logger.warning(f'Action message edit bo‘lmadi: {e}')

    else:
        # Oddiy single-post holat
        try:
            if call.message.caption is not None:
                await call.message.edit_caption(
                    caption=sold_caption,
                    reply_markup=None,
                )
            else:
                await call.message.edit_text('✅ Sotildi', reply_markup=None)
        except Exception as e:
            logger.warning(f'Post edit bo‘lmadi: {e}')

    owner_chat_id = int(updated['user_id'])
    notify_text = (
        "✅ Mashinangiz sotildi deb belgilandi.\n"
        f"ID: {car_id}\n"
        f"Model: {updated.get('model')}"
    )

    try:
        await bot.send_message(owner_chat_id, notify_text)
    except Exception as e:
        logger.warning(f'Ega uchun notification yuborilmadi: {e}')

    await _notify_admins(
        "💸 Mashina sotildi\n"
        f"ID: {car_id}\n"
        f"Model: {updated.get('model')}\n"
        f"Narx: {updated.get('price')}$\n"
        f"Ega ID: {updated.get('user_id')}"
    )

    await call.answer('E’lon sotilgan deb belgilandi!')

@router.message(AddCarStates.photos)
async def invalid_photo(message: Message) -> None:
    await message.answer("⚠️ Iltimos rasm yuboring yoki 'tayyor' deb yozing.")


@router.message(AddCarStates.model)
@router.message(AddCarStates.condition)
@router.message(AddCarStates.transmission)
@router.message(AddCarStates.color)
@router.message(AddCarStates.region)
async def invalid_text(message: Message) -> None:
    await message.answer('⚠️ Iltimos matn yuboring!')


@router.message(AddCarStates.price)
@router.message(AddCarStates.mileage)
async def invalid_number(message: Message) -> None:
    await message.answer('⚠️ Iltimos faqat raqam yuboring!')
