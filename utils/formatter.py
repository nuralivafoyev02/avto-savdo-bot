from html import escape

def format_car(data: dict) -> str:
    username = (data.get('username') or '').strip()
    username_line = f"👤 Telegram: @{escape(username)}\n" if username else ''
    return (
        f"🚗 <b>{escape(str(data.get('model', 'Noma’lum')))}</b>\n"
        f"💰 Narx: <b>{escape(str(data.get('price', 0)))}$</b>\n"
        f"⚙️ Holati: {escape(str(data.get('condition', '—')))}\n"
        f"🔧 Uzatma: {escape(str(data.get('transmission', '—')))}\n"
        f"🎨 Rang: {escape(str(data.get('color', '—')))}\n"
        f"📏 Probeg: {escape(str(data.get('mileage', '—')))} km\n"
        f"📍 Hudud: {escape(str(data.get('region', '—')))}\n\n"
        f"📞 Aloqa: {escape(str(data.get('phone', '—')))}\n"
        f"{username_line}"
        f"📷 Rasmlar soni: {len(data.get('photos') or ([data.get('photo')] if data.get('photo') else []))}"
    )
