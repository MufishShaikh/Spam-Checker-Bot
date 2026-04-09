import time
import requests
import os

# ---------------------------------------------------------
# SETUP: TELEGRAM TOKEN
# (Now reads from an environment variable for security)
# ---------------------------------------------------------
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN_HERE")

# Local or Cloud backend URL
API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

# Render changes the port dynamically, so we must grab it from the environment!
PORT = os.environ.get("PORT", "8000")
SPAM_API_URL = f"http://127.0.0.1:{PORT}/classify"

def get_updates(offset=None):
    """Fetches new messages from Telegram API"""
    url = f"{API_URL}/getUpdates"
    params = {"timeout": 100, "offset": offset}
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching updates: {e}")
        return None

def send_message(chat_id, text):
    """Sends a message back to the user via Telegram"""
    url = f"{API_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Error sending message: {e}")

def check_spam(message_text):
    """Sends the message to the FastAPI backend to classify"""
    try:
        response = requests.post(SPAM_API_URL, json={"message": message_text})
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error calling Spam API: {e}")
        return None

def main():
    print("🤖 Telegram Bot is starting...")
    
    if TELEGRAM_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        print("\n❌ ERROR: You haven't added your Telegram Token!")
        print("Please open 'telegram_bot.py' and replace 'YOUR_TELEGRAM_BOT_TOKEN_HERE'")
        print("with the token you got from BotFather.\n")
        return

    print("✅ Bot is running! Make sure your FastAPI backend is also running.")
    last_update_id = None
    
    while True:
        updates = get_updates(offset=last_update_id)
        
        if updates and "result" in updates:
            for update in updates["result"]:
                # Increment update_id to acknowledge message receipt
                last_update_id = update["update_id"] + 1
                
                # Check if it is a text message
                if "message" in update and "text" in update["message"]:
                    chat_id = update["message"]["chat"]["id"]
                    text = update["message"]["text"]
                    
                    if text == "/start":
                        send_message(chat_id, "🤖 Hello! Forward me any message and I'll tell you if it's spam.")
                        continue
                        
                    print(f"Received message to check: '{text[:30]}...'")
                    
                    # 1. Classify the text
                    result = check_spam(text)
                    
                    # 2. Reply to user
                    if result:
                        is_spam = result["is_spam"]
                        confidence = round(result["confidence"] * 100, 1)
                        processing_time = result["processing_time_ms"]
                        
                        if is_spam:
                            reply = f"🚨 <b>SPAM DETECTED!</b>\n\nI am {confidence}% confident this is a scam/spam message.\n<i>(Processed in {processing_time}ms)</i>"
                        else:
                            reply = f"✅ <b>SAFE (Not Spam)</b>\n\nThis looks like a normal message ({confidence}% confidence).\n<i>(Processed in {processing_time}ms)</i>"
                            
                        send_message(chat_id, reply)
                    else:
                        send_message(chat_id, "❌ Error connecting to Spam Detection API. Is the backend running?")
        
        time.sleep(1)

if __name__ == '__main__':
    main()
