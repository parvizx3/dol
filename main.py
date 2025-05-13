import os
import re
import requests
from bs4 import BeautifulSoup
import hashlib

# === Config ===
BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
DEST_CHANNELS = os.getenv("DEST_CHANNEL").split("|")
SOURCE_URLS = os.getenv("SOURCE_URL").split("|")
BLACKLIST = [w.strip().lower() for w in os.getenv("BLACKLIST", "").split("|") if w.strip()]
WHITELIST = [w.strip().lower() for w in os.getenv("WHITELIST", "").split("|") if w.strip()]
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
    text = re.sub(r'\n+', '\n', text)
    text = re.sub(r'(?<=\S)\n(?=\S)', ' ', text)
    text = text.replace("\n", "")
    return text.strip()

def get_messages_from_web(url):
    res = requests.get(url)
    soup = BeautifulSoup(res.text, 'html.parser')
    messages = []
    msg_links = []
    
    for msg_bubble in soup.select('.tgme_widget_message_bubble'):
        date_link = msg_bubble.select_one('.tgme_widget_message_footer a.tgme_widget_message_date')
        message_url = date_link['href'] if date_link else None
        msg_links.append(message_url)
        
        msg_text_element = msg_bubble.select_one('.tgme_widget_message_text')
        if msg_text_element:
            text = msg_text_element.get_text(separator="\n").strip()
            if text:
                cleaned = clean_message(text)
                messages.append(cleaned)
    
    return messages, msg_links

def send_message_to_channel(text, chat_id):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": text,
        "disable_web_page_preview": True,
        "disable_notification": True
    }
    response = requests.post(url, data=data)
    return response.ok

def get_hash(text):
    return hashlib.sha256(text.encode()).hexdigest()

# === Run ===
for source_url, dest_channel in zip(SOURCE_URLS, DEST_CHANNELS):
    messages, divs = get_messages_from_web(source_url)
    # messages.reverse()  # Uncomment if needed
    for i in range(len(messages)):
        msg = messages[i]
        msg_hash = get_hash(divs[i]) if divs[i] else None
        
        if not msg_hash or msg_hash in sent_hashes:
            continue
            
        if not is_blacklisted(msg) and is_whitelisted(msg):
            if send_message_to_channel(msg, dest_channel):
                print(f"✅ Sent to {dest_channel}: {msg[:50]}...")
                with open(SENT_HASH_FILE, "a") as f:
                    f.write(msg_hash + "\n")
            else:
                print(f"❌ Failed to send to {dest_channel}: {msg[:50]}")
        else:
            print(f"⏭️ Skipped (filtered) in {dest_channel}: {msg[:50]}")
