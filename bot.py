import json
import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters
)

# Aapki Credentials
BOT_TOKEN = "8880070789:AAHeaqAfMpW_tQBFtaoAuUSile3bPKwmowE"
ADMIN_ID = 8457000157

# Payment Details
EASYPAISA_NO = "03215150976"
BINANCE_ID = "991923035"
WHATSAPP_NO = "+923215150976"

# JSON Files
DB_FILE = "products.json"
REF_DB_FILE = "ref_products.json"
USERS_FILE = "users.json"
POINTS_FILE = "user_points.json"
CODES_FILE = "promo_codes.json"

# State tracking for waiting code input
WAITING_FOR_CODE = {}

# --- DATABASE HANDLING ---

def load_json(file_path, default_value):
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            return json.load(f)
    save_json(file_path, default_value)
    return default_value

def save_json(file_path, data):
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_user(user_id):
    users = load_users()
    if user_id not in users:
        users.add(user_id)
        with open(USERS_FILE, "w") as f:
            json.dump(list(users), f)

# Paid & Free Stores
default_paid = {
    "1": {"name": "Gemini Advanced (18 Months)", "price": "450 PKR / $2"},
    "2": {"name": "ChatGPT Plus", "price": "1000 PKR"}
}

default_ref_products = {
    "1": {"name": "Gemini 18 Months Redeem Link", "points": 1, "stocks": ["https://gemini.google.com/redeem?code=TEST12345"]}
}

products_db = load_json(DB_FILE, default_paid)
ref_products_db = load_json(REF_DB_FILE, default_ref_products)
user_points = load_json(POINTS_FILE, {})
promo_codes = load_json(CODES_FILE, {})  # {"BONUS100": {"points": 1, "limit": 100, "used_by": []}}

# --- USER FUNCTIONS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_id_str = str(user_id)
    save_user(user_id)
    WAITING_FOR_CODE.pop(user_id, None)
    
    # Referral track
    args = context.args
    referrer_id = None
    if args and args[0].startswith("ref_"):
        referrer_id = args[0].replace("ref_", "")

    if user_id_str not in user_points:
        user_points[user_id_str] = 1
        save_json(POINTS_FILE, user_points)

        if referrer_id and referrer_id != user_id_str and referrer_id in user_points:
            user_points[referrer_id] = user_points.get(referrer_id, 0) + 1
            save_json(POINTS_FILE, user_points)
            
            try:
                await context.bot.send_message(
                    chat_id=int(referrer_id),
                    text=f"🎉 **Referral Confirmed!**\nAapke link se naye user ne join kiya hai.\n🎁 **+1 Point Added!** Total Points: `{user_points[referrer_id]}`",
                    parse_mode='Markdown'
                )
            except Exception:
                pass

    points = user_points.get(user_id_str, 0)
    
    keyboard = [
        [InlineKeyboardButton("📦 Selling Products (Paid)", callback_data='user_products')],
        [InlineKeyboardButton("🎁 Free Referral Rewards Store", callback_data='redeem_product')],
        [InlineKeyboardButton("🎟️ Redeem Gift Code", callback_data='enter_promo')],
        [InlineKeyboardButton("🔗 My Referral Link & Points", callback_data='ref_system')],
        [InlineKeyboardButton("📞 Contact Support", callback_data='user_support')]
    ]
    
    if user_id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("⚙️ Admin Panel", callback_data='admin_panel')])

    reply_markup = InlineKeyboardMarkup(keyboard)
    welcome_text = (
        f"👋 **Khushamdeed!**\n\n"
        f"🎁 Aap ke paas **{points} Referral Point(s)** available hain.\n\n"
        "Neeche diye gaye options se chunein:"
    )
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    user_id_str = str(user_id)
    bot_username = (await context.bot.get_me()).username
    save_user(user_id)
    WAITING_FOR_CODE.pop(user_id, None)
    await query.answer()

    points = user_points.get(user_id_str, 0)

    if query.data == 'user_products':
        if not products_db:
            text = "❌ Filhaal koi selling product available nahi hai."
            keyboard = [[InlineKeyboardButton("🔙 Back", callback_data='back_to_main')]]
        else:
            text = "🔥 **Available Products For Sale:**\n\n"
            keyboard = []
            for p_id, item in products_db.items():
                text += f"{p_id}. **{item['name']}** — `{item['price']}`\n"
                keyboard.append([InlineKeyboardButton(f"💳 Buy #{p_id} {item['name']}", callback_data=f'buy_{p_id}')])
            text += "\nKhareedne ke liye button par click karein."
            keyboard.append([InlineKeyboardButton("🔙 Back", callback_data='back_to_main')])

        await query.edit_message_text(text=text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == 'redeem_product':
        if not ref_products_db:
            text = "❌ Filhaal koi free reward available nahi hai."
            keyboard = [[InlineKeyboardButton("🔙 Back", callback_data='back_to_main')]]
        else:
            text = f"🎁 **FREE Referral Products Store**\n👤 **Aapke Total Points:** `{points}`\n\n"
            keyboard = []
            for r_id, item in ref_products_db.items():
                req_pts = item.get('points', 1)
                stock_count = len(item.get('stocks', []))
                text += f"🔹 **#{r_id} {item['name']}**\n🎯 Required Points: `{req_pts} Pts` | Stock: `{stock_count}`\n\n"
                keyboard.append([InlineKeyboardButton(f"🎁 Claim {item['name']} ({req_pts} Pts)", callback_data=f'confirm_redeem_{r_id}')])
            keyboard.append([InlineKeyboardButton("🔙 Back", callback_data='back_to_main')])

        await query.edit_message_text(text=text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.startswith('confirm_redeem_'):
        r_id = query.data.split('_')[2]
        ref_product = ref_products_db.get(r_id)
        if not ref_product:
            await query.answer("❌ Product nahi mila!", show_alert=True)
            return

        req_pts = ref_product.get('points', 1)

        if points < req_pts:
            ref_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
            text = (
                f"❌ **Points Kam Hain!**\n\n"
                f"Is product ke liye **{req_pts} Points** chahiye.\n"
                f"Aapke paas sirf **{points} Points** hain.\n\n"
                f"Naye points ke liye apna link share karein:\n🔗 `{ref_link}`"
            )
            keyboard = [[InlineKeyboardButton("🔙 Back", callback_data='redeem_product')]]
            await query.edit_message_text(text=text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
            return
            
        if not ref_product.get('stocks'):
            text = f"⚠️ **Stock Out!**\n\nAfsos! **{ref_product['name']}** ka stock khatam hai."
            keyboard = [[InlineKeyboardButton("🔙 Back", callback_data='redeem_product')]]
            await query.edit_message_text(text=text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
            return

        delivered_item = ref_product['stocks'].pop(0)
        save_json(REF_DB_FILE, ref_products_db)

        user_points[user_id_str] = points - req_pts
        save_json(POINTS_FILE, user_points)

        ref_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
        text = (
            f"🎉 **FREE REWARD CLAIMED SUCCESSFULLY!** 🎉\n\n"
            f"📦 **Reward:** {ref_product['name']}\n"
            f"💰 **Points Used:** {req_pts} Point(s)\n"
            f"🎁 **Remaining Points:** {user_points[user_id_str]}\n\n"
            f"🔑 **YOUR PRODUCT LINK / ACCOUNT CREDENTIALS:**\n"
            f"`{delivered_item}`\n\n"
            f"💡 **More Rewards:** Referral link share karein:\n`{ref_link}`"
        )
        keyboard = [[InlineKeyboardButton("🔙 Main Menu", callback_data='back_to_main')]]
        await query.edit_message_text(text=text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == 'enter_promo':
        WAITING_FOR_CODE[user_id] = True
        text = (
            "🎟️ **Redeem Gift Code**\n\n"
            "Apna Promo Code chat mein likh kar bhej dein:\n"
            "*(Example: `BONUS100`)*"
        )
        keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data='back_to_main')]]
        await query.edit_message_text(text=text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == 'ref_system':
        ref_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
        text = (
            f"💎 **Referral & Points System**\n\n"
            f"👤 **Aapke Total Points:** `{points}`\n\n"
            f"🔗 **Aapka Referral Link:**\n`{ref_link}`"
        )
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data='back_to_main')]]
        await query.edit_message_text(text=text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.startswith('buy_'):
        p_id = query.data.split('_')[1]
        product = products_db.get(p_id)
        text = (
            f"🛒 **Selected Selling Product #{p_id}:** {product['name']}\n"
            f"💰 **Price:** {product['price']}\n\nSelect Payment Method:"
        )
        keyboard = [
            [InlineKeyboardButton("📲 EasyPaisa", callback_data=f'pay_easypaisa_{p_id}')],
            [InlineKeyboardButton("🟡 Binance (Crypto)", callback_data=f'pay_binance_{p_id}')],
            [InlineKeyboardButton("🔙 Back", callback_data='user_products')]
        ]
        await query.edit_message_text(text=text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.startswith('pay_easypaisa_'):
        p_id = query.data.split('_')[2]
        product = products_db.get(p_id)
        text = (
            f"💳 **EasyPaisa Details**\n\n📦 **Product #{p_id}:** {product['name']}\n💵 **Amount:** {product['price']}\n\n"
            f"📱 **EasyPaisa Number:** `{EASYPAISA_NO}`\n\nScreenshot WhatsApp Karein: `{WHATSAPP_NO}`"
        )
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data='user_products')]]
        await query.edit_message_text(text=text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.startswith('pay_binance_'):
        p_id = query.data.split('_')[2]
        product = products_db.get(p_id)
        text = (
            f"🟡 **Binance Details**\n\n📦 **Product #{p_id}:** {product['name']}\n💵 **Amount:** {product['price']}\n\n"
            f"🆔 **Binance Pay ID:** `{BINANCE_ID}`\n\nScreenshot WhatsApp Karein: `{WHATSAPP_NO}`"
        )
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data='user_products')]]
        await query.edit_message_text(text=text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == 'user_support':
        text = f"📞 **Customer Support:**\nWhatsApp Karein: `{WHATSAPP_NO}`"
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data='back_to_main')]]
        await query.edit_message_text(text=text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == 'back_to_main':
        keyboard = [
            [InlineKeyboardButton("📦 Selling Products (Paid)", callback_data='user_products')],
            [InlineKeyboardButton("🎁 Free Referral Rewards Store", callback_data='redeem_product')],
            [InlineKeyboardButton("🎟️ Redeem Gift Code", callback_data='enter_promo')],
            [InlineKeyboardButton("🔗 My Referral Link & Points", callback_data='ref_system')],
            [InlineKeyboardButton("📞 Contact Support", callback_data='user_support')]
        ]
        if user_id == ADMIN_ID:
            keyboard.append([InlineKeyboardButton("⚙️ Admin Panel", callback_data='admin_panel')])
            
        welcome_text = (
            f"👋 **Khushamdeed!**\n\n"
            f"🎁 Aap ke paas **{points} Referral Point(s)** available hain.\n\n"
            "Neeche diye gaye options se chunein:"
        )
        await query.edit_message_text(text=welcome_text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == 'admin_panel':
        if user_id != ADMIN_ID:
            return
        admin_text = (
            "⚙️ **Admin Control Panel**\n\n"
            "💵 **Add Paid Product:** `/add Product Name | Price`\n"
            "❌ **Delete Paid Product:** `/delete ID`\n\n"
            "🎁 **Add Free Ref Product:** `/addref Product Name | Points | Content`\n"
            "🗑️ **Delete Free Ref Product:** `/deleteref ID`\n\n"
            "🎟️ **Create Redeem Code:**\n`/makecode Code | Points | Limit`\n"
            "*(Example: `/makecode BONUS100 | 1 | 50`)*\n\n"
            "❌ **Delete Redeem Code:**\n`/delcode Code`"
        )
        keyboard = [
            [InlineKeyboardButton("📋 View All Products & Codes", callback_data='admin_view_products')],
            [InlineKeyboardButton("🔙 Main Menu", callback_data='back_to_main')]
        ]
        await query.edit_message_text(text=admin_text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == 'admin_view_products':
        if user_id != ADMIN_ID:
            return
        text = "📋 **Paid Selling Products:**\n"
        for p_id, item in products_db.items():
            text += f"🔹 #{p_id} — {item['name']} (`{item['price']}`)\n"

        text += "\n🎁 **Free Referral Store:**\n"
        for r_id, item in ref_products_db.items():
            s_count = len(item.get('stocks', []))
            pts = item.get('points', 1)
            text += f"🔹 #{r_id} — {item['name']} (`{pts} Pts`) | Stock: `{s_count}`\n"

        text += "\n🎟️ **Active Promo Codes:**\n"
        if not promo_codes:
            text += "Koi promo code active nahi hai."
        else:
            for code, data in promo_codes.items():
                used_count = len(data.get('used_by', []))
                text += f"🔑 `{code}` — Points: `{data['points']}` | Used: `{used_count}/{data['limit']}`\n"

        keyboard = [[InlineKeyboardButton("🔙 Back to Admin Panel", callback_data='admin_panel')]]
        await query.edit_message_text(text=text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))


# --- PROMO CODE TEXT HANDLER ---

async def handle_text_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_id_str = str(user_id)
    
    # Check if user clicked Redeem Code button
    if WAITING_FOR_CODE.get(user_id):
        WAITING_FOR_CODE[user_id] = False
        entered_code = update.message.text.strip()

        if entered_code not in promo_codes:
            await update.message.reply_text("❌ **Invalid Promo Code!** Code sahi likhein ya expired ho chuka hai.", parse_mode='Markdown')
            return

        code_info = promo_codes[entered_code]
        used_by = code_info.get('used_by', [])

        # Check if already used by user
        if user_id_str in used_by:
            await update.message.reply_text("⚠️ **Aap yeh code pehle hi claim kar chuke hain!**", parse_mode='Markdown')
            return

        # Check limit
        if len(used_by) >= code_info['limit']:
            await update.message.reply_text("❌ **Code Expired!** Is code ki limit poori ho chuki hai.", parse_mode='Markdown')
            return

        # Success! Add Points & save record
        add_pts = code_info['points']
        user_points[user_id_str] = user_points.get(user_id_str, 0) + add_pts
        save_json(POINTS_FILE, user_points)

        code_info['used_by'].append(user_id_str)
        save_json(CODES_FILE, promo_codes)

        await update.message.reply_text(
            f"🎉 **CONGRATULATIONS! CODE REDEEMED!** 🎉\n\n"
            f"🎁 **Bonus Added:** +{add_pts} Point(s)\n"
            f"👤 **Total Points Now:** `{user_points[user_id_str]}`\n\n"
            f"Ab aap Free Rewards Store se apna reward claim kar sakte hain!",
            parse_mode='Markdown'
        )


# --- ADMIN COMMANDS ---

async def make_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        raw_text = " ".join(context.args)
        code, points_str, limit_str = raw_text.split("|")
        code = code.strip()
        points = int(points_str.strip())
        limit = int(limit_str.strip())

        promo_codes[code] = {
            "points": points,
            "limit": limit,
            "used_by": []
        }
        save_json(CODES_FILE, promo_codes)

        await update.message.reply_text(
            f"✅ **Promo Code Created Successfully!**\n\n"
            f"🔑 **Code:** `{code}`\n"
            f"🎁 **Reward Points:** {points}\n"
            f"👥 **User Limit:** {limit} Users",
            parse_mode='Markdown'
        )
    except Exception:
        await update.message.reply_text("❌ **Format:** `/makecode CODE | Points | Limit`\n\nExample:\n`/makecode BONUS100 | 1 | 50`", parse_mode='Markdown')

async def del_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if not context.args:
        await update.message.reply_text("❌ Code likhein. Example: `/delcode BONUS100`", parse_mode='Markdown')
        return
    code = context.args[0].strip()
    if code in promo_codes:
        promo_codes.pop(code)
        save_json(CODES_FILE, promo_codes)
        await update.message.reply_text(f"🗑️ Promo Code `{code}` delete kar diya gaya hai!", parse_mode='Markdown')
    else:
        await update.message.reply_text("❌ Yeh code exist nahi karta.")

async def add_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        raw_text = " ".join(context.args)
        name, price = raw_text.split("|")
        existing_ids = [int(k) for k in products_db.keys()] if products_db else [0]
        new_id = str(max(existing_ids) + 1)
        products_db[new_id] = {"name": name.strip(), "price": price.strip()}
        save_json(DB_FILE, products_db)
        await update.message.reply_text(f"✅ Selling Product Added! ID: #{new_id}")
    except Exception:
        await update.message.reply_text("❌ Format: `/add Product Name | Price`")

async def add_ref_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        raw_text = " ".join(context.args)
        name, points_str, stock_data = raw_text.split("|")
        name = name.strip()
        points = int(points_str.strip())
        stock_data = stock_data.strip()

        found_id = None
        for r_id, item in ref_products_db.items():
            if item['name'].lower() == name.lower():
                found_id = r_id
                break

        if not found_id:
            existing_ids = [int(k) for k in ref_products_db.keys()] if ref_products_db else [0]
            found_id = str(max(existing_ids) + 1)
            ref_products_db[found_id] = {"name": name, "points": points, "stocks": []}
        else:
            ref_products_db[found_id]["points"] = points

        ref_products_db[found_id]["stocks"].append(stock_data)
        save_json(REF_DB_FILE, ref_products_db)

        current_stock = len(ref_products_db[found_id]["stocks"])
        await update.message.reply_text(f"✅ Referral Reward Added! ID: #{found_id} | Stock: {current_stock}")
    except Exception:
        await update.message.reply_text("❌ Format: `/addref Product Name | Points | Content`", parse_mode='Markdown')

async def delete_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if not context.args:
        return
    p_id = context.args[0]
    if p_id in products_db:
        products_db.pop(p_id)
        save_json(DB_FILE, products_db)
        await update.message.reply_text(f"🗑️ Selling Product #{p_id} removed!")

async def delete_ref_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if not context.args:
        return
    r_id = context.args[0]
    if r_id in ref_products_db:
        ref_products_db.pop(r_id)
        save_json(REF_DB_FILE, ref_products_db)
        await update.message.reply_text(f"🗑️ Referral Product #{r_id} removed!")

def main():
    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .connect_timeout(30.0)
        .read_timeout(30.0)
        .write_timeout(30.0)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add_product))
    app.add_handler(CommandHandler("addref", add_ref_product))
    app.add_handler(CommandHandler("delete", delete_product))
    app.add_handler(CommandHandler("deleteref", delete_ref_product))
    app.add_handler(CommandHandler("makecode", make_code))
    app.add_handler(CommandHandler("delcode", del_code))
    
    app.add_handler(CallbackQueryHandler(handle_buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_messages))

    print("Bot with Custom Promo Code Generator is Running...")
    app.run_polling()

if __name__ == '__main__':
    main()