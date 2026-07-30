import json
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters

# Logging Setup
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# File Paths
USERS_FILE = 'users.json'
POINTS_FILE = 'user_points.json'
REF_PRODUCTS_FILE = 'ref_products.json'

# Load / Save Helpers
def load_json(filename):
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_json(filename, data):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)

# Start Command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    users = load_json(USERS_FILE)
    
    users[str(user.id)] = {
        "username": user.username,
        "first_name": user.first_name
    }
    save_json(USERS_FILE, users)

    keyboard = [
        [InlineKeyboardButton("🛍️ Buy Products", callback_data="buy_products")],
        [InlineKeyboardButton("💎 My Account / Points", callback_data="my_account")],
        [InlineKeyboardButton("🎟️ Redeem Promo Code", callback_data="redeem_promo")],
        [InlineKeyboardButton("📞 Support / Help", callback_data="support")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_text = (
        f"Assalam-o-Alaikum *{user.first_name}*! 👋\n\n"
        "Welcome to our digital products store bot.\n"
        "Select an option below to proceed:"
    )
    
    if update.callback_query:
        await update.callback_query.message.edit_text(welcome_text, parse_mode='Markdown', reply_markup=reply_markup)
    else:
        await update.message.reply_text(welcome_text, parse_mode='Markdown', reply_markup=reply_markup)

# Callback Router
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "buy_products":
        keyboard = [
            [InlineKeyboardButton(" Canva Pro", callback_data="prod_canva")],
            [InlineKeyboardButton(" Netflix / Prime", callback_data="prod_streaming")],
            [InlineKeyboardButton("⬅️ Back to Menu", callback_data="main_menu")]
        ]
        await query.message.edit_text("🛍️ *Select a category or product:*", parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "prod_canva":
        keyboard = [
            [InlineKeyboardButton("💳 Pay via Easypaisa", callback_data="pay_easypaisa")],
            [InlineKeyboardButton("🪙 Pay via Binance ($)", callback_data="pay_binance")],
            [InlineKeyboardButton("⬅️ Back", callback_data="buy_products")]
        ]
        text = (
            "📌 *Canva Pro Lifetime/Subscription*\n\n"
            "Price: $3 or Rs. 850\n"
            "Please choose your payment method below:"
        )
        await query.message.edit_text(text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "pay_easypaisa":
        text = (
            "💳 *Easypaisa Payment Details*\n\n"
            "Account Name: **Ahmed Iftikhar**\n"
            "Account Number: `03001234567` *(Example number, update if needed)*\n\n"
            "⚠️ *Instructions:* Send payment and send the screenshot/Transaction ID to admin for manual verification."
        )
        keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="buy_products")]]
        await query.message.edit_text(text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "pay_binance":
        text = (
            "🪙 *Binance Payment Details*\n\n"
            "Binance Name: **ahmad819**\n"
            "Binance Pay ID / USDT Address: `123456789` *(Example)*\n\n"
            "⚠️ *Instructions:* Send the exact amount in **$**, and share the TxID/Screenshot with admin."
        )
        keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="buy_products")]]
        await query.message.edit_text(text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "my_account":
        user_id = str(query.from_user.id)
        points_data = load_json(POINTS_FILE)
        user_pts = points_data.get(user_id, 0)
        
        text = (
            f"👤 *Your Account Info*\n\n"
            f"ID: `{user_id}`\n"
            f"Points / Balance: *{user_pts}*\n"
        )
        keyboard = [[InlineKeyboardButton("⬅️ Back to Menu", callback_data="main_menu")]]
        await query.message.edit_text(text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "redeem_promo":
        text = "🎟️ To redeem a promo code, please contact the admin directly or type your code format."
        keyboard = [[InlineKeyboardButton("⬅️ Back to Menu", callback_data="main_menu")]]
        await query.message.edit_text(text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "support":
        text = "📞 For support and order verification, contact admin: @ahmadsaith"
        keyboard = [[InlineKeyboardButton("⬅️ Back to Menu", callback_data="main_menu")]]
        await query.message.edit_text(text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "main_menu":
        await start(update, context)

# Main Function
def main():
    TOKEN = "YOUR_BOT_TOKEN_HERE" # Apna Bot Token yahan daalein agar zaroorat ho
    
    # Agar aap python-telegram-bot v20+ use kar rahe hain:
    # app = ApplicationBuilder().token("YOUR_TOKEN").build()
    # Lekin filhal aap apni purani working initialization use kar sakte hain ya yeh:
    
    print("Bot is ready...")

if __name__ == '__main__':
    # Yahan aap apna run script ya app.run() rakhein jo pehle se chal raha hai
    pass