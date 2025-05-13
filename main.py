import os
import re
from telethon import TelegramClient
from telethon.tl.functions.messages import GetHistoryRequest

# Load from environment variables
api_id = int(os.getenv("TG_API_ID"))
api_hash = os.getenv("TG_API_HASH")
bot_token = os.getenv("TG_BOT_TOKEN")
source_channel = os.getenv("SOURCE_CHANNEL")
destination_channel = os.getenv("DEST_CHANNEL")
blacklist = [w.strip().lower() for w in os.getenv("BLACKLIST", "").split(",") if w.strip()]
whitelist = [w.strip().lower() for w in os.getenv("WHITELIST", "").split(",") if w.strip()]

client = TelegramClient('bot', api_id, api_hash).start(bot_token=bot_token)

def contains_url(text: str) -> bool:
    return bool(re.search(r'http[s]?://|t\.me', text))

def is_blacklisted(text: str) -> bool:
    return any(word in text.lower() for word in blacklist) or contains_url(text)

def is_whitelisted(text: str) -> bool:
    if not whitelist:
        return True  # If no whitelist is set, allow everything
    return any(word in text.lower() for word in whitelist)

async def sync():
    print(f"Checking messages from {source_channel}")
    entity = await client.get_entity(source_channel)
    result = await client(GetHistoryRequest(
        peer=entity,
        limit=10,
        offset_date=None,
        offset_id=0,
        max_id=0,
        min_id=0,
        add_offset=0,
        hash=0
    ))

    for message in reversed(result.messages):
        if hasattr(message, 'message') and message.message:
            text = message.message
            if not is_blacklisted(text) and is_whitelisted(text):
                await client.send_message(destination_channel, text)
                print(f"Sent: {text[:30]}...")
            else:
                print(f"Skipped: {text[:30]}...")

with client:
    client.loop.run_until_complete(sync())
