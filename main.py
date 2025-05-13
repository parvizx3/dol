import os
import re
from telethon import TelegramClient, events
from telethon.tl.functions.messages import GetHistoryRequest

# Load from environment variables
api_id = int(os.getenv("TG_API_ID"))
api_hash = os.getenv("TG_API_HASH")
bot_token = os.getenv("TG_BOT_TOKEN")
source_channel = os.getenv("SOURCE_CHANNEL")  # e.g. 'publicchannelname'
destination_channel = os.getenv("DEST_CHANNEL")  # e.g. '@my_private_channel'
blacklist = os.getenv("BLACKLIST", "").split(",")  # comma-separated words

client = TelegramClient('bot', api_id, api_hash).start(bot_token=bot_token)

def contains_url_or_blacklist(text: str) -> bool:
    if any(word.lower() in text.lower() for word in blacklist):
        return True
    if re.search(r'http[s]?://|t\.me', text):
        return True
    return False

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
            if not contains_url_or_blacklist(text):
                await client.send_message(destination_channel, text)
            else:
                print(f"Skipped: {text[:30]}...")

with client:
    client.loop.run_until_complete(sync())
