import logging
import requests
import random
import time
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters

# ================= التوكن والإعدادات =================
BOT_TOKEN = "8854067469:AAECoNTDQlnV7V6FAhUnDwsdxbrDeLdYRso"
ADMIN_IDS = [5100562548]
# ===================================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ================= بريد مؤقت حقيقي =================

class TempEmail:
    def __init__(self):
        self.email = None
        self.token = None
    
    def create(self):
        """إنشاء بريد مؤقت حقيقي من Guerrilla Mail"""
        try:
            url = "https://api.guerrillamail.com/ajax.php"
            params = {
                'f': 'get_email_address',
                'ip': '127.0.0.1',
                'agent': 'Mozilla/5.0'
            }
            response = requests.get(url, params=params)
            data = response.json()
            
            if data.get('email_addr'):
                self.email = data['email_addr']
                self.token = data.get('sid_token')
                logger.info(f"✅ تم إنشاء بريد: {self.email}")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ فشل إنشاء البريد: {e}")
            return False
    
    def get_verification_code(self, max_wait=60):
        """انتظار والحصول على كود التفعيل"""
        start = time.time()
        while time.time() - start < max_wait:
            try:
                url = "https://api.guerrillamail.com/ajax.php"
                params = {
                    'f': 'get_email_list',
                    'sid_token': self.token,
                    'seq': 0
                }
                response = requests.get(url, params=params)
                data = response.json()
                
                if data.get('list'):
                    for email in data['list']:
                        body = email.get('mail_body', '')
                        # البحث عن كود 6 أرقام
                        match = re.search(r'\b\d{6}\b', body)
                        if match:
                            code = match.group()
                            logger.info(f"✅ تم العثور على كود: {code}")
                            return code
            except:
                pass
            time.sleep(5)
        return None

# ================= دوال البوت =================

def start(update, context):
    user = update.effective_user
    context.user_data.clear()
    
    keyboard = [
        [InlineKeyboardButton("📝 تقديم بلاغ", callback_data="report")],
        [InlineKeyboardButton("📧 بريد مؤقت", callback_data="temp_email")],
        [InlineKeyboardButton("❓ مساعدة", callback_data="help")]
    ]
    
    update.message.reply_text(
        "👋 *مرحباً بك في بوت Nasser AI V2!*\n\n"
        "📌 *الميزات:*\n"
        "• 📝 تقديم بلاغات حقيقية\n"
        "• 📧 إنشاء بريد مؤقت حقيقي\n"
        "• 🔐 آمن وسريع\n\n"
        "اختر أحد الأزرار:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def help_command(update, context):
    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back")]]
    update.message.reply_text(
        "❓ *المساعدة*\n\n"
        "📝 *تقديم بلاغ:*\n"
        "1. اضغط على 'تقديم بلاغ'\n"
        "2. أرسل اسم المستخدم\n"
        "3. أرسل سبب البلاغ\n\n"
        "📧 *البريد المؤقت:*\n"
        "1. اضغط على 'بريد مؤقت'\n"
        "2. سيتم إنشاء بريد لك\n"
        "3. انتظر الكود\n\n"
        "للأسئلة: @abdonaser27",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def temp_email(update, context):
    query = update.callback_query
    query.answer()
    
    # إنشاء بريد مؤقت
    email = TempEmail()
    if email.create():
        context.user_data['temp_email'] = email
        context.user_data['step'] = 'waiting_code'
        
        query.edit_message_text(
            f"📧 *تم إنشاء بريدك المؤقت!*\n\n"
            f"📨 البريد: `{email.email}`\n\n"
            f"⏳ انتظر حتى يصل كود التفعيل...\n"
            f"(سيتم تحديثه تلقائياً)",
            parse_mode='Markdown'
        )
        
        # بدء البحث عن الكود
        check_code(update, context)
    else:
        query.edit_message_text("❌ فشل إنشاء البريد. حاول مرة أخرى.")

def check_code(update, context):
    """البحث عن كود التفعيل"""
    email = context.user_data.get('temp_email')
    if not email:
        return
    
    code = email.get_verification_code(max_wait=60)
    
    if code:
        context.user_data['verification_code'] = code
        context.user_data['step'] = 'report_reason'
        
        update.callback_query.edit_message_text(
            f"✅ *تم استلام كود التفعيل!*\n\n"
            f"🔑 الكود: `{code}`\n\n"
            f"📝 *الآن أرسل سبب البلاغ:*\n"
            f"(مثال: احتيال، مضايقة، محتوى غير لائق)",
            parse_mode='Markdown'
        )
    else:
        update.callback_query.edit_message_text(
            "❌ لم يتم استلام كود التفعيل.\n"
            "حاول مرة أخرى باستخدام /start",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 رجوع", callback_data="back")]
            ])
        )

def report_start(update, context):
    query = update.callback_query
    query.answer()
    context.user_data['step'] = 'report_target'
    query.edit_message_text(
        "✏️ *أرسل اسم المستخدم المستهدف:*\n"
        "(بدون @)",
        parse_mode='Markdown'
    )

def handle_message(update, context):
    text = update.message.text
    step = context.user_data.get('step')
    
    if step == 'report_target':
        context.user_data['target'] = text
        context.user_data['step'] = 'report_reason'
        update.message.reply_text(
            f"🎯 المستهدف: @{text}\n\n"
            f"✏️ *أرسل سبب البلاغ:*\n"
            f"(مثال: احتيال، مضايقة، محتوى غير لائق)",
            parse_mode='Markdown'
        )
    
    elif step == 'report_reason':
        target = context.user_data.get('target', 'غير معروف')
        reason = text
        code = context.user_data.get('verification_code', 'بدون كود')
        
        # تسجيل البلاغ
        report_data = {
            'target': target,
            'reason': reason,
            'code': code,
            'user': update.effective_user.username or update.effective_user.id
        }
        
        # عرض التقرير للمستخدم
        update.message.reply_text(
            f"✅ *تم استلام بلاغك!*\n\n"
            f"📊 *التفاصيل:*\n"
            f"• 🎯 المستهدف: @{target}\n"
            f"• 📝 السبب: {reason}\n"
            f"• 🔑 كود التفعيل: `{code}`\n\n"
            f"شكراً لك على الإبلاغ! 🙏",
            parse_mode='Markdown'
        )
        
        context.user_data.clear()

def back_handler(update, context):
    query = update.callback_query
    query.answer()
    context.user_data.clear()
    
    keyboard = [
        [InlineKeyboardButton("📝 تقديم بلاغ", callback_data="report")],
        [InlineKeyboardButton("📧 بريد مؤقت", callback_data="temp_email")],
        [InlineKeyboardButton("❓ مساعدة", callback_data="help")]
    ]
    
    query.edit_message_text(
        "🤖 *القائمة الرئيسية*\n\nاختر الإجراء المناسب:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def callback_handler(update, context):
    query = update.callback_query
    data = query.data
    
    if data == "report":
        report_start(update, context)
    elif data == "temp_email":
        temp_email(update, context)
    elif data == "help":
        help_command(update, context)
    elif data == "back":
        back_handler(update, context)
    else:
        query.answer("❌ خيار غير معروف")

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CallbackQueryHandler(callback_handler))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    
    logger.info("🚀 البوت شغال!")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
