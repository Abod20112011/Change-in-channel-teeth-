import os
import requests
import time
from datetime import datetime
import pytz

# ======================== قراءة المتغيرات من البيئة ========================
TOKEN = os.environ.get("TOKEN", "")
CHANNEL_USERNAME = os.environ.get("CHANNEL_USERNAME", "")
TIMEZONE_STR = os.environ.get("TIMEZONE", "Asia/Baghdad")

if not TOKEN or not CHANNEL_USERNAME:
    print("❌ خطأ: TOKEN و CHANNEL_USERNAME مطلوبان")
    exit(1)

# توقيت
timezone = pytz.timezone(TIMEZONE_STR)

# ======================== دوال تحويل الأرقام ========================
def convert_to_bold_unicode(number_str):
    bold_digits = {
        '0': '𝟬', '1': '𝟭', '2': '𝟮', '3': '𝟯', '4': '𝟰',
        '5': '𝟱', '6': '𝟲', '7': '𝟳', '8': '𝟴', '9': '𝟵'
    }
    result = ''
    for char in number_str:
        if char in bold_digits:
            result += bold_digits[char]
        else:
            result += char
    return result

def get_formatted_time():
    now = datetime.now(timezone)
    hour = now.hour
    minute = now.minute
    
    # تحويل إلى 12 ساعة
    if hour == 0:
        hour_12 = 12
        period = "ص"
    elif hour == 12:
        hour_12 = 12
        period = "م"
    elif hour > 12:
        hour_12 = hour - 12
        period = "م"
    else:
        hour_12 = hour
        period = "ص"
    
    time_str = f"{hour_12:02d}:{minute:02d}"
    bold_time = convert_to_bold_unicode(time_str)
    
    return f"𓏺 {bold_time} . {period}"

# ======================== حذف آخر رسالة ========================
def delete_last_message():
    try:
        get_updates_url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
        params = {
            "chat_id": CHANNEL_USERNAME,
            "limit": 10,
            "allowed_updates": ["channel_post"]
        }
        
        response = requests.get(get_updates_url, params=params)
        updates = response.json()
        
        if updates.get("ok") and updates.get("result"):
            for update in reversed(updates["result"]):
                if "channel_post" in update:
                    message_id = update["channel_post"]["message_id"]
                    
                    delete_url = f"https://api.telegram.org/bot{TOKEN}/deleteMessage"
                    delete_data = {
                        "chat_id": CHANNEL_USERNAME,
                        "message_id": message_id
                    }
                    
                    delete_response = requests.post(delete_url, json=delete_data)
                    result = delete_response.json()
                    
                    if result.get("ok"):
                        print(f"🗑️ تم حذف آخر رسالة (ID: {message_id})")
                        return True
                    else:
                        return False
            return False
    except Exception as e:
        print(f"⚠️ خطأ في الحذف: {e}")
        return False

# ======================== تغيير اسم القناة ========================
def rename_channel():
    try:
        new_name = get_formatted_time()
        current_time = datetime.now(timezone).strftime("%H:%M:%S")
        print(f"[{current_time}] تغيير الاسم إلى: {new_name}")
        
        url = f"https://api.telegram.org/bot{TOKEN}/setChatTitle"
        data = {"chat_id": CHANNEL_USERNAME, "title": new_name}
        
        response = requests.post(url, data=data)
        result = response.json()
        
        if result.get("ok"):
            print(f"✅ تم تغيير الاسم بنجاح")
            time.sleep(1)
            delete_last_message()
        else:
            print(f"❌ فشل تغيير الاسم: {result.get('description')}")
            
    except Exception as e:
        print(f"⚠️ خطأ: {e}")

# ======================== التشغيل الرئيسي ========================
def main():
    print("="*60)
    print("🚀 بوت تغيير اسم القناة التلقائي")
    print("="*60)
    print(f"📢 القناة: {CHANNEL_USERNAME}")
    print(f"⏱️ التغيير كل دقيقة")
    print(f"🌍 المنطقة الزمنية: {TIMEZONE_STR}")
    print("="*60)
    
    rename_channel()
    
    try:
        while True:
            time.sleep(60)
            rename_channel()
    except KeyboardInterrupt:
        print("\n🛑 تم إيقاف البوت يدوياً.")

if __name__ == "__main__":
    main()
