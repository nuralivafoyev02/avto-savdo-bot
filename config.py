import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN', '').strip()
CHANNEL_ID_RAW = os.getenv('CHANNEL_ID', '').strip()
DB_FILE = os.getenv('DB_FILE', 'bot_database.db')

ADMIN_IDS_RAW = os.getenv('ADMIN_IDS', '').strip()
ADMIN_IDS = {
    int(item.strip())
    for item in ADMIN_IDS_RAW.split(',')
    if item.strip().isdigit()
}

if not BOT_TOKEN:
    raise ValueError('BOT_TOKEN .env faylda kiritilmagan')

if not CHANNEL_ID_RAW:
    raise ValueError('CHANNEL_ID .env faylda kiritilmagan')

CHANNEL_ID = int(CHANNEL_ID_RAW)
