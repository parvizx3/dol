import os
import re
import requests
import time
from bs4 import BeautifulSoup
import hashlib
from datetime import datetime
# === Config ===
BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
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
    message_elements = []
    
    for msg_div in soup.select('.tgme_widget_message_text'):
        # Store the raw element for hashing
        element_str = str(msg_div)
        text = msg_div.get_text(separator="\n").strip()
        
        if text:
            cleaned = clean_message(text)
            # Store both the element and cleaned text
            messages.append((element_str, cleaned))
    
    return messages
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
def get_hash(element):
    return hashlib.sha256(element.encode()).hexdigest()
# === Run ===
messages = get_messages_from_web(SOURCE_URL)
#messages.reverse()  # Send in correct order
new_hashes = []
for element_str, msg_text in messages:
    # Hash the entire element instead of just the text
    element_hash = get_hash(element_str)
    
    if element_hash in sent_hashes:
        continue
        
    if not is_blacklisted(msg_text) and is_whitelisted(msg_text):
        if send_message_to_channel(msg_text):
            print(f"✅ Sent: {msg_text[:50]}...")
            new_hashes.append(element_hash)
        else:
            print(f"❌ Failed to send: {msg_text[:50]}")
    else:
        print(f"⏭️ Skipped (filtered): {msg_text[:50]}")
# Save new hashes
if new_hashes:
    with open(SENT_HASH_FILE, "a") as f:
        for h in new_hashes:
            f.write(h + "\n")
