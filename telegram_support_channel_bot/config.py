import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.getenv("BOT_TOKEN")
ADMIN_ID: int = int(os.getenv("ADMIN_ID"))
CHANNEL_ID: str = os.getenv("CHANNEL_ID")
