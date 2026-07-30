import json
import logging
import os
from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# ================= Configuration =================
TOKEN = "8880070789:AAHeaqAfMpW_tQBFtaoAuUSile3bPKwmowE"
ADMIN_ID = 8457000157

# Products Catalogue (Price per item RS mein)
PRODUCTS = {
    "gemini": {"name": "Google Gemini 18-Month", "price": 450},
    "nordvpn": {"name": "NordVPN Account", "price": 300},
    "canva": {"name": "Canva Pro Invite", "price": 200},
    "duolingo": {"name": "Super Duolingo", "price": 250},
}

# Payment Details
EASYPAISA_NO = "03215150976"
EASYPAISA_NAME = "Ahmed Iftikhar"

BINANCE_PAY_ID = "9919230335"
BINANCE_NAME = "ahmad819"

WHATSAPP_CONTACT = "+923215150976"

DATA_FILE = "data.json"
USERS_FILE = "users.json"

WAITING_FOR_PROMO = range(1)


# ================= Database Helpers =================


def load_data():
  if not os.path.exists(DATA_FILE):
    return {
        "users": {},
        "stock": {key: [] for key in PRODUCTS},
        "promos": {},
    }
  with open(DATA_FILE, "r") as f:
    try:
      data = json.load(f)
      if "stock" not in data:
        data["stock"] = {}
      if "promos" not in data:
        data["promos"] = {}
      for key in PRODUCTS:
        if key not in data["stock"]:
          data["stock"][key] = []
      return data
    except Exception:
      return {
          "users": {},
          "stock": {key: [] for key in PRODUCTS},
          "promos": {},
      }


def save_data(data):
  with open(DATA_FILE, "w") as f:
    json.dump(data, f, indent=4)


def record_user_activity(user_id):
  users = set()
  if os.path.exists(USERS_FILE):
    with open(USERS_FILE, "r") as f:
      try:
        users = set(json.load(f))
      except Exception:
        users = set()
  if user_id not in users:
    users.add(user_id)
    with open(USERS_FILE, "w") as f:
      json.dump(list(users), f)


# ================= Main Handlers =================


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
  user = update.effective_user
  user_id = str(user.id)
  record_user_activity(user.id)

  data = load_data()
  if user_id not in data["users"]:
    data["users"][user_id] = {}
    save_data(data)

  keyboard = [
      [
          InlineKeyboardButton("🛍️ Browse Store", callback_data="btn_store"),
          InlineKeyboardButton(
              "🎟️ Redeem Code", callback_data="btn_redeem_menu"
          ),
      ],
      [
          InlineKeyboardButton("👤 My Profile", callback_data="btn_profile"),
          InlineKeyboardButton("📞 Support", callback_data="btn_support"),
      ],
  ]

  if user_id == str(ADMIN_ID):
    keyboard.append(
        [InlineKeyboardButton("👑 Admin Panel", callback_data="btn_admin_panel")]
    )

  welcome_msg = (
      f"✨ **Assalam-o-Alaikum, {user.first_name}!** 👋\n\n"
      f"🤖 Welcome to our **Automated Store Bot** 🚀\n"
      f"💎 Browse products, make payment, send screenshot on WhatsApp, and get your product via Promo Code!\n\n"
      f"👇 Please select an option from below:"
  )

  if update.message:
    await update.message.reply_text(
        welcome_msg,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )
  elif update.callback_query:
    await update.callback_query.message.edit_text(
        welcome_msg,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )
  return ConversationHandler.END


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
  query = update.callback_query
  await query.answer()

  user_id = str(query.from_user.id)
  data = load_data()

  if query.data == "btn_profile":
    msg = (
        f"👤 **Aapki Profile Details:**\n\n"
        f"🆔 **User ID:** `{user_id}`\n"
        f"✨ **Status:** Verified Customer 🌟"
    )
    keyboard = [
        [
            InlineKeyboardButton(
                "🎟️ Redeem Promo Code", callback_data="btn_redeem_menu"
            )
        ],
        [InlineKeyboardButton("🔙 Main Menu", callback_data="btn_main")],
    ]
    await query.message.edit_text(
        msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
    )

  elif query.data == "btn_admin_panel" and user_id == str(ADMIN_ID):
    stk_summary = "📦 **Live Stock Overview:**\n\n"
    for idx, (key, pinfo) in enumerate(PRODUCTS.items(), start=1):
      stk_len = len(data["stock"].get(key, []))
      stk_summary += f"{idx}: {pinfo['name']} | `{pinfo['price']} RS` ({stk_len} in stock)\n"

    msg = (
        f"👑 **Admin Control & Management Panel** ⚡\n\n"
        f"{stk_summary}\n"
        f"🛠️ **Admin Commands:**\n"
        f"• Add Stock: `/addstock [key] item1\\nitem2`\n"
        f"• Delete Stock: `/delstock [key] [index]`\n"
        f"• View Stock: `/stock`\n"
        f"• Create Promo: `/createpromo [prod_key] [qty] [price_pkr] [price_usd] [CODE] [limit] [days]`\n"
        f"• View Promos: `/promos`\n"
        f"• Delete Promo: `/delpromo [CODE]`"
    )
    keyboard = [[InlineKeyboardButton("🔙 Main Menu", callback_data="btn_main")]]
    await query.message.edit_text(
        msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
    )

  elif query.data == "btn_store":
    msg = (
        f"🛍️ **Digital Store Catalog** 🌟\n\n"
        f"Select a product to view pricing & payment gateways:\n\n"
    )
    keyboard = []

    for idx, (key, pinfo) in enumerate(PRODUCTS.items(), start=1):
      stk_len = len(data["stock"].get(key, []))
      btn_text = (
          f"{idx}: {pinfo['name']} | {pinfo['price']} RS ({stk_len} in stock)"
      )
      keyboard.append(
          [InlineKeyboardButton(btn_text, callback_data=f"view_prod_{key}")]
      )

    keyboard.append(
        [InlineKeyboardButton("🔙 Main Menu", callback_data="btn_main")]
    )
    await query.message.edit_text(
        msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
    )

  elif query.data.startswith("view_prod_"):
    prod_key = query.data.replace("view_prod_", "")
    pinfo = PRODUCTS.get(prod_key)

    if pinfo:
      stock_count = len(data["stock"].get(prod_key, []))
      idx_num = list(PRODUCTS.keys()).index(prod_key) + 1
      msg = (
          f"📦 **Product & Pricing Details:**\n\n"
          f"🔹 **Item:** {idx_num}: {pinfo['name']}\n"
          f"💵 **Price:** `{pinfo['price']} RS`\n"
          f"📊 **Available Stock:** `{stock_count} Units`\n\n"
          f"💳 **Payment Gateways (Jis par payment karni hai):**\n\n"
          f"📱 **EasyPaisa / JazzCash:**\n"
          f"• Number: `{EASYPAISA_NO}`\n"
          f"• Name: `{EASYPAISA_NAME}`\n\n"
          f"🟡 **Binance Pay ID:**\n"
          f"• Pay ID: `{BINANCE_PAY_ID}`\n"
          f"• Name: `{BINANCE_NAME}`\n\n"
          f"📸 **Important Step:**\n"
          f"Payment karne ke baad apna **Screenshot** is WhatsApp number par bhejein: `{WHATSAPP_CONTACT}`\n"
          f"Admin aap ko WhatsApp par **Promo Code** dega jo yahan redeem karke aap product hasil kar sakenge!"
      )
      keyboard = [
          [InlineKeyboardButton("🔙 Back to Store", callback_data="btn_store")]
      ]
      await query.message.edit_text(
          msg,
          reply_markup=InlineKeyboardMarkup(keyboard),
          parse_mode="Markdown",
      )

  elif query.data == "btn_redeem_menu":
    await query.message.edit_text(
        f"🎟️ **Promo Code Redemption** 🎁\n\n"
        f"Apna promo code jo admin ne WhatsApp par diya hai yahan enter karein:",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Main Menu", callback_data="btn_main")
        ]]),
    )
    context.user_data["waiting_promo"] = True

  elif query.data == "btn_support":
    msg = (
        f"📞 **Customer Support & Help Desk** 💬\n\n"
        f"Koi bhi masla ho ya payment ka screenshot bhejna ho, direct WhatsApp par rabta karein:\n\n"
        f"📱 **WhatsApp Support:** `{WHATSAPP_CONTACT}`"
    )
    keyboard = [[InlineKeyboardButton("🔙 Main Menu", callback_data="btn_main")]]
    await query.message.edit_text(
        msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
    )

  elif query.data == "btn_main":
    await start(update, context)


# ================= Redeem Handler =================


async def handle_promo_redemption(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
  user = update.effective_user
  user_id = str(user.id)
  text = update.message.text.strip().upper()

  if not context.user_data.get("waiting_promo"):
    return

  context.user_data["waiting_promo"] = False
  data = load_data()
  promos = data["promos"]

  if text not in promos:
    await update.message.reply_text(
        "❌ **Invalid Promo Code!** Sahi code enter karein.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Main Menu", callback_data="btn_main")
        ]]),
    )
    return ConversationHandler.END

  promo_info = promos[text]
  expiry_date = datetime.fromisoformat(promo_info["expiry"])

  if datetime.now() > expiry_date:
    await update.message.reply_text(
        "⏳ **Promo Code Expired!** Yeh code abhi expired ho chuka hai.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Main Menu", callback_data="btn_main")
        ]]),
    )
    return ConversationHandler.END

  # Check if user has already redeemed this specific code
  if "redeemed_users" not in promo_info:
    promo_info["redeemed_users"] = []

  if user_id in promo_info["redeemed_users"]:
    await update.message.reply_text(
        "⚠️ **Already Redeemed!** Aap yeh promo code pehle hi use kar chuke hain, yeh sirf 1 bar redeem ho sakta hai.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Main Menu", callback_data="btn_main")
        ]]),
    )
    return ConversationHandler.END

  if promo_info["uses"] <= 0:
    await update.message.reply_text(
        "⚠️ **Limit Reached!** Is promo code ki total usage limit khatam ho chuki hai.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Main Menu", callback_data="btn_main")
        ]]),
    )
    return ConversationHandler.END

  prod_key = promo_info["product_key"]
  required_qty = promo_info["qty"]
  stock = data["stock"].get(prod_key, [])

  if len(stock) < required_qty:
    await update.message.reply_text(
        f"❌ **Stock Kam Hai!** Is code ke liye `{required_qty}` items chahiyein lekin stock mein sirf `{len(stock)}` hain. Admin se rabta karein.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Main Menu", callback_data="btn_main")
        ]]),
    )
    return ConversationHandler.END

  # Extract exact required quantity step-by-step from stock
  bought_items = []
  for _ in range(required_qty):
    bought_items.append(stock.pop(0))

  # Update promo uses and track redeemed user
  promo_info["uses"] -= 1
  promo_info["redeemed_users"].append(user_id)
  data["stock"][prod_key] = stock
  save_data(data)

  pinfo = PRODUCTS.get(prod_key, {"name": prod_key})
  
  # Step-by-step display format for customer items/links
  items_str = "\n".join(
      [f"🔹 **Link {idx+1}:** `{item}`" for idx, item in enumerate(bought_items)]
  )

  await update.message.reply_text(
      f"🎉 **Promo Code Successfully Redeemed!** 🎊\n\n"
      f"📦 **Product:** {pinfo['name']}\n"
      f"🔢 **Quantity / Links:** `{required_qty}`\n\n"
      f"🔑 **Aapke Credentials / Links (Step-by-Step):**\n{items_str}\n\n"
      f"🙏 Thank you for buying from us!",
      parse_mode="Markdown",
  )

  try:
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=(
            f"🔔 **PROMO CODE REDEEMED!** 🛍️\n\n"
            f"👤 **User:** {user.first_name} (`{user_id}`)\n"
            f"🎟️ **Code:** `{text}`\n"
            f"🔹 **Product:** {pinfo['name']} (Qty: {required_qty})"
        ),
        parse_mode="Markdown",
    )
  except Exception:
    pass

  return ConversationHandler.END


async def cancel_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
  context.user_data.clear()
  await update.message.reply_text("❌ Action Cancelled.")
  return ConversationHandler.END


# ================= Admin Management Commands =================


async def add_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
  if update.effective_user.id != ADMIN_ID:
    return

  if not context.args:
    msg = "⚠️ **Syntax:** `/addstock [PRODUCT_KEY]`\n\n**Product Keys:**\n"
    for idx, k in enumerate(PRODUCTS, start=1):
      msg += f"• `{k}` ({idx}: {PRODUCTS[k]['name']})\n"
    await update.message.reply_text(msg, parse_mode="Markdown")
    return

  prod_key = context.args[0].lower()
  if prod_key not in PRODUCTS:
    await update.message.reply_text("❌ Invalid Product Key!")
    return

  if len(context.args) > 1:
    raw_text = " ".join(context.args[1:])
    lines = [
        line.strip() for line in raw_text.split("\n") if line.strip()
    ]
    data = load_data()
    for item in lines:
      data["stock"][prod_key].append(item)
    save_data(data)

    await update.message.reply_text(
        f"✅ **Stock Added Successfully!** 📦\n\n"
        f"🔹 Product: {PRODUCTS[prod_key]['name']}\n"
        f"➕ Added: `{len(lines)}` items\n"
        f"📊 Total Stock: `{len(data['stock'][prod_key])} Available`",
        parse_mode="Markdown",
    )
  else:
    await update.message.reply_text(
        f"⚠️ Items nahi diye.\nSahi tareeqa: `/addstock nordvpn user:pass`",
        parse_mode="Markdown",
    )


async def delete_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
  if update.effective_user.id != ADMIN_ID:
    return

  if len(context.args) < 2:
    await update.message.reply_text(
        "⚠️ **Syntax:** `/delstock [PRODUCT_KEY] [INDEX]`\nExample:"
        " `/delstock gemini 0`",
        parse_mode="Markdown",
    )
    return

  prod_key = context.args[0].lower()
  try:
    index = int(context.args[1])
  except ValueError:
    await update.message.reply_text("❌ Index number hona chahiye (jaise: 0, 1)")
    return

  if prod_key not in PRODUCTS:
    await update.message.reply_text("❌ Invalid Product Key!")
    return

  data = load_data()
  stock_list = data["stock"].get(prod_key, [])

  if index < 0 or index >= len(stock_list):
    await update.message.reply_text(
        f"❌ Galat index! Is product mein sirf `{len(stock_list)}` items hain"
        f" (0 se {len(stock_list)-1} tak)."
    )
    return

  removed_item = stock_list.pop(index)
  data["stock"][prod_key] = stock_list
  save_data(data)

  await update.message.reply_text(
      f"🗑️ **Stock Item Deleted!**\n📦 Product: {PRODUCTS[prod_key]['name']}\n❌ Deleted: `{removed_item}`",
      parse_mode="Markdown",
  )


async def check_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
  if update.effective_user.id != ADMIN_ID:
    return

  data = load_data()
  msg = "📦 **Live Stock & Numbered Items Summary:** 📊\n\n"
  for idx, (key, pinfo) in enumerate(PRODUCTS.items(), start=1):
    stk_list = data["stock"].get(key, [])
    msg += f"🔹 **{idx}: {pinfo['name']}** (`{key}`): `{len(stk_list)} Items`\n"
    for i, item in enumerate(stk_list):
      msg += f"   [{i}]: `{item}`\n"
    msg += "\n"

  await update.message.reply_text(msg, parse_mode="Markdown")


# ================= Promo Code Admin Commands =================


async def create_promo(update: Update, context: ContextTypes.DEFAULT_TYPE):
  if update.effective_user.id != ADMIN_ID:
    return

  # Syntax: /createpromo [prod_key] [qty] [price_pkr] [price_usd] [CODE] [limit] [days]
  if len(context.args) < 7:
    await update.message.reply_text(
        "⚠️ **Invalid Syntax!**\n\n"
        "Sahi tareeqa yeh hai:\n"
        "`/createpromo [prod_key] [qty] [price_pkr] [price_usd] [CODE] [limit]"
        " [days]`\n\n"
        "**Example:**\n"
        "`/createpromo gemini 1 450 1.65 GEMINI500 1 7`",
        parse_mode="Markdown",
    )
    return

  prod_key = context.args[0].lower()
  if prod_key not in PRODUCTS:
    await update.message.reply_text(
        f"❌ Invalid Product Key! Sahi keys hain: {list(PRODUCTS.keys())}"
    )
    return

  try:
    qty = int(context.args[1])
    price_pkr = int(context.args[2])
    price_usd = float(context.args[3])
    code = context.args[4].upper()
    limit = int(context.args[5])
    days = int(context.args[6])
  except ValueError:
    await update.message.reply_text(
        "❌ Qty, PKR Price, Limit aur Days numbers mein aur USD price decimal"
        " mein honi chahiye!"
    )
    return

  expiry = datetime.now() + timedelta(days=days)

  data = load_data()
  data["promos"][code] = {
      "product_key": prod_key,
      "qty": qty,
      "price_pkr": price_pkr,
      "price_usd": price_usd,
      "uses": limit,
      "expiry": expiry.isoformat(),
      "redeemed_users": [],
  }
  save_data(data)

  await update.message.reply_text(
      f"🎟️ **Custom Promo Code Created Successfully!** 🌟\n\n"
      f"🏷️ **Code:** `{code}`\n"
      f"📦 **Product:** {PRODUCTS[prod_key]['name']}\n"
      f"🔢 **Quantity / Links:** `{qty}`\n"
      f"💵 **Price:** `{price_pkr} PKR` | `\u0024{price_usd}`\n"
      f"👥 **User Limit:** `{limit}`\n"
      f"⏳ **Expiry:** `{expiry.strftime('%Y-%m-%d %H:%M')}`",
      parse_mode="Markdown",
  )


async def list_promos(update: Update, context: ContextTypes.DEFAULT_TYPE):
  if update.effective_user.id != ADMIN_ID:
    return

  data = load_data()
  promos = data.get("promos", {})

  if not promos:
    await update.message.reply_text(
        "📂 Koi active promo code maujood nahi hai."
    )
    return

  msg = "🎟️ **Active Promo Codes List:** 📋\n\n"
  for code, info in promos.items():
    exp_date = datetime.fromisoformat(info["expiry"]).strftime(
        "%Y-%m-%d %H:%M"
    )
    pname = PRODUCTS.get(info["product_key"], {}).get("name", "Unknown")
    msg += (
        f"🏷️ **Code:** `{code}`\n"
        f"• Product: `{pname}`\n"
        f"• Qty/Links: `{info.get('qty', 1)}`\n"
        f"• Price: `{info.get('price_pkr', 0)} PKR` |"
        f" `\u0024{info.get('price_usd', 0)}`\n"
        f"• Remaining Uses: `{info['uses']}`\n"
        f"• Expires: `{exp_date}`\n\n"
    )

  await update.message.reply_text(msg, parse_mode="Markdown")


async def delete_promo(update: Update, context: ContextTypes.DEFAULT_TYPE):
  if update.effective_user.id != ADMIN_ID:
    return

  if not context.args:
    await update.message.reply_text(
        "⚠️ **Syntax:** `/delpromo [CODE]`\nExample: `/delpromo GEMINI500`",
        parse_mode="Markdown",
    )
    return

  code = context.args[0].upper()
  data = load_data()

  if code in data.get("promos", {}):
    del data["promos"][code]
    save_data(data)
    await update.message.reply_text(
        f"🗑️ Promo code `{code}` successfully delete kar diya gaya hai!"
    )
  else:
    await update.message.reply_text(
        f"❌ Promo code `{code}` list mein nahi mila."
    )


# ================= Main Function =================


def main():
  app = ApplicationBuilder().token(TOKEN).build()

  # Redeem Input Conversation Handler
  conv_handler = ConversationHandler(
      entry_points=[
          CallbackQueryHandler(button_handler, pattern="^btn_redeem_menu$")
      ],
      states={
          WAITING_FOR_PROMO: [
              MessageHandler(
                  filters.TEXT & ~filters.COMMAND, handle_promo_redemption
              )
          ]
      },
      fallbacks=[CommandHandler("cancel", cancel_action)],
  )

  app.add_handler(conv_handler)
  app.add_handler(CommandHandler("start", start))
  app.add_handler(CommandHandler("addstock", add_stock))
  app.add_handler(CommandHandler("delstock", delete_stock))
  app.add_handler(CommandHandler("stock", check_stock))
  app.add_handler(CommandHandler("createpromo", create_promo))
  app.add_handler(CommandHandler("promos", list_promos))
  app.add_handler(CommandHandler("delpromo", delete_promo))
  app.add_handler(CallbackQueryHandler(button_handler))

  print("Store & Custom Promo Bot is Running Perfectly...")
  app.run_polling()


if __name__ == "__main__":
  main()