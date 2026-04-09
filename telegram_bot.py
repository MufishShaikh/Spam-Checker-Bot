import time
import requests
import os

# ---------------------------------------------------------
# SETUP: TELEGRAM TOKEN
# (Now reads from an environment variable for security)
# ---------------------------------------------------------
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN_HERE")

# Telegram API URL
API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

# Use Render's public URL if we are in the cloud, otherwise fallback to local port
EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL")
if EXTERNAL_URL:
    API_BASE = EXTERNAL_URL
else:
    PORT = os.environ.get("PORT", "8000")
    API_BASE = f"http://127.0.0.1:{PORT}"

SPAM_API_URL = f"{API_BASE}/classify"
FEEDBACK_API_URL = f"{API_BASE}/feedback"
STATS_API_URL = f"{API_BASE}/stats"

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

def send_message(chat_id, text, reply_markup=None):
    """Sends a message back to the user via Telegram"""
    url = f"{API_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        payload["reply_markup"] = reply_markup
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

def get_stats():
    try:
        response = requests.get(STATS_API_URL)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error getting stats: {e}")
        return None

def send_feedback(message_id):
    try:
        requests.post(FEEDBACK_API_URL, json={"message_id": message_id})
    except Exception as e:
        print(f"Error sending feedback: {e}")

def answer_callback(callback_id, text):
    url = f"{API_URL}/answerCallbackQuery"
    requests.post(url, json={"callback_query_id": callback_id, "text": text})

def edit_message_text(chat_id, message_id, text):
    url = f"{API_URL}/editMessageText"
    requests.post(url, json={"chat_id": chat_id, "message_id": message_id, "text": text, "parse_mode": "HTML"})

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
                
                # Handle button clicks (Feedback)
                if "callback_query" in update:
                    cb = update["callback_query"]
                    cb_data = cb.get("data", "")
                    if cb_data.startswith("mistake_"):
                        msg_id = int(cb_data.split("_")[1])
                        send_feedback(msg_id)
                        answer_callback(cb["id"], "Thanks! Feedback recorded.")
                        # Edit message to signify feedback was received
                        chat_id = cb["message"]["chat"]["id"]
                        message_id = cb["message"]["message_id"]
                        old_text = cb["message"]["text"]
                        edit_message_text(chat_id, message_id, old_text + "\n\n<i>[Feedback Recorded]</i>")
                    continue
                
                # Check if it is a text message
                if "message" in update and "text" in update["message"]:
                    chat_id = update["message"]["chat"]["id"]
                    text = update["message"]["text"]
                    
                    if text == "/start":
                        send_message(chat_id, "🤖 Hello! Forward me any message and I'll tell you if it's spam.\n\nType /stats to see global analytics!")
                        continue
                        
                    if text == "/stats":
                        stats = get_stats()
                        if stats:
                            msg = f"📊 <b>Live Analytics Hub</b>\n\n"
                            msg += f"• Total Messages Scanned: <b>{stats['total_scanned']}</b>\n"
                            msg += f"• Identified Spam: {stats['total_spam']}\n"
                            msg += f"• Safe Messages: {stats['total_safe']}\n"
                            msg += f"• Mistakes Corrected via Feedback: {stats['mistakes_reported']}\n"
                            msg += f"• System Accuracy: <b>{stats['accuracy_rate']}%</b>\n"
                            send_message(chat_id, msg)
                        else:
                            send_message(chat_id, "❌ Error retrieving stats from database.")
                        continue
                        
                    print(f"Received message to check: '{text[:30]}...'")
                    
                    # 1. Classify the text
                    result = check_spam(text)
                    
                    # 2. Reply to user
                    if result:
                        is_spam = result["is_spam"]
                        confidence = round(result["confidence"] * 100, 1)
                        processing_time = result["processing_time_ms"]
                        db_msg_id = result["message_id"]
                        
                        if is_spam:
                            reply = f"🚨 <b>SPAM DETECTED!</b>\n\nI am {confidence}% confident this is a scam/spam message.\n<i>(Processed in {processing_time}ms)</i>"
                        else:
                            reply = f"✅ <b>SAFE (Not Spam)</b>\n\nThis looks like a normal message ({confidence}% confidence).\n<i>(Processed in {processing_time}ms)</i>"
                            
                        # Add inline button for feedback
                        markup = {
                            "inline_keyboard": [[{"text": "❌ Bot made a mistake", "callback_data": f"mistake_{db_msg_id}"}]]
                        }
                        send_message(chat_id, reply, reply_markup=markup)
                    else:
                        send_message(chat_id, "❌ Error connecting to Spam Detection API. Is the backend running?")
        
        time.sleep(1)

if __name__ == '__main__':
    main()
