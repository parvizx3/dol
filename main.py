import os
import re
import requests
from bs4 import BeautifulSoup
import hashlib
# === Config ===
BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
DEST_CHANNEL = os.getenv("DEST_CHANNEL")
SOURCE_URL = os.getenv("SOURCE_URL")  # e.g. https://t.me/s/publicchannelusername
BLACKLIST = [w.strip().lower() for w in os.getenv("BLACKLIST", "").split(",") if w.strip()]
WHITELIST = [w.strip().lower() for w in os.getenv("WHITELIST", "").split(",") if w.strip()]
SENT_HASH_FILE = "sent_hashes.txt"
# === Load sent hashes ===
if os.path.exists(SENT_HASH_FILE):
    with open(SENT_HASH_FILE, "r") as f:
        sent_hashes = set(line.strip() for line in f if line.strip())
else:
    sent_hashes = set()
def contains_url(text):
    return bool(re.search(r'http[s]?://|t\.me', text))
def is_blacklisted(text):
    return any(word in text.lower() for word in BLACKLIST) or contains_url(text)
def is_whitelisted(text):
    if not WHITELIST:
        return True
    return any(word in text.lower() for word in WHITELIST)
def clean_message(text):
    # Collapse multiple line breaks
    text = re.sub(r'\n+', '\n', text)
    # Remove line breaks between emoji/symbols/numbers/words
    # Example: "⏳\n83,400\nخــرید" → "⏳ 83,400 خــرید"
    text = re.sub(r'(?<=\S)\n(?=\S)', ' ', text)
    text = text.replace("\n", "")
    return text.strip()
def get_messages_from_web(url):
    res = requests.get(url)
    soup = BeautifulSoup(res.text, 'html.parser')
    messages = []
    msg_divs = []
    for msg_div in soup.select('.tgme_widget_message'):
        msg_divs.append(str(msg_div))
        msg_div = msg_div.select('.tgme_widget_message')
        text = msg_div.get_text(separator="\n").strip()
        if text:
            cleaned = clean_message(text)
            messages.append(cleaned)
    return messages, msg_divs
def send_message_to_channel(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": DEST_CHANNEL,
        "text": text,
        "disable_web_page_preview": True,
        "disable_notification": True  # 🔕 Silent message
    }
    response = requests.post(url, data=data)
    return response.ok
def get_hash(text):
    return hashlib.sha256(text.encode()).hexdigest()
# === Run ===
messages, divs = get_messages_from_web(SOURCE_URL)
#messages.reverse()  # Send in correct order
i=0
for msg in messages:
    msg_hash = get_hash(divs[i])
    if msg_hash in sent_hashes:
        continue
    if not is_blacklisted(msg) and is_whitelisted(msg):
        if send_message_to_channel(msg):
            print(f"✅ Sent: {msg[:50]}...")
            with open(SENT_HASH_FILE, "a") as f:
                f.write(msg_hash + "\n")
        else:
            print(f"❌ Failed to send: {msg[:50]}")
    else:
        print(f"⏭️ Skipped (filtered): {msg[:50]}")
    i += 1
