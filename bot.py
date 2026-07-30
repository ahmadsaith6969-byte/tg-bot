import json
import logging
import os
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

# Updated Payment & Support Details
EASYPAISA_NO = "03215150976"
EASYPAISA_NAME = "Ahmed Iftikhar"

BINANCE_PAY_ID = "9919230335"
BINANCE_NAME = "ahmad819"

SUPPORT_CONTACT = "+923215150976"

DATA_FILE = "data.json"
USERS_FILE = "users.json"

WAITING_FOR_AMOUNT, WAITING_FOR_TID, WAITING_FOR_QTY = range(3)


# ================= Database Helpers =================


def load_data():
  if not os.path.exists(DATA_FILE):
    return {"users": {}, "stock": {key: [] for key in PRODUCTS}}
  with open(DATA_FILE, "r") as f:
    try:
      data = json.load(f)
      if "stock" not in data:
        data["stock"] = {}
      for key in PRODUCTS:
        if key not in data["stock"]:
          data["stock"][key] = []
      return data
    except Exception:
      return {"users": {}, "stock": {key: [] for key in PRODUCTS}}


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
    data["users"][user_id] = {"balance": 0}
    save_data(data)

  keyboard = [
      [
          InlineKeyboardButton("🛍️ Browse Store", callback_data="btn_store"),
          InlineKeyboardButton("💳 Wallet / Deposit", callback_data="btn_wallet"),
      ],
      [
          InlineKeyboardButton("👤 Profile", callback_data="btn_profile"),
          InlineKeyboardButton(
              "📞 Contact Support", callback_data="btn_support"
          ),
      ],
  ]

  if user_id == str(ADMIN_ID):
    keyboard.append(
        [InlineKeyboardButton("👑 Admin Panel", callback_data="btn_admin_panel")]
    )

  welcome_msg = (
      f"Aoa **{user.first_name}**! 👋\n\n"
      "Welcome to our Automated Digital Store Bot!\n"
      "Niche diye gaye options mein se select karein:"
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
  user_info = data["users"].get(user_id, {"balance": 0})

  if query.data == "btn_profile":
    msg = (
        f"👤 **Aapki Profile:**\n\n"
        f"🆔 **User ID:** `{user_id}`\n"
        f"💰 **Wallet Balance:** `{user_info['balance']} RS`\n"
    )
    keyboard = [
        [
            InlineKeyboardButton(
                "➕ Deposit Money", callback_data="btn_wallet"
            )
        ],
        [InlineKeyboardButton("🔙 Main Menu", callback_data="btn_main")],
    ]
    await query.message.edit_text(
        msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
    )

  elif query.data == "btn_admin_panel" and user_id == str(ADMIN_ID):
    stk_summary = "📦 **Admin Stock Summary:**\n\n"
    for key, pinfo in PRODUCTS.items():
      stk_len = len(data["stock"].get(key, []))
      stk_summary += f"• {pinfo['name']} (`{key}`): `{stk_len} Available`\n"

    msg = (
        f"👑 **Admin Control Panel**\n\n"
        f"{stk_summary}\n"
        f"💡 **Commands:**\n"
        f"• Add Stock: `/addstock [key] item1\nitem2`\n"
        f"• Delete Stock: `/delstock [key] [index]`\n"
        f"• Check Stock: `/stock`"
    )
    keyboard = [[InlineKeyboardButton("🔙 Main Menu", callback_data="btn_main")]]
    await query.message.edit_text(
        msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
    )

  elif query.data == "btn_store":
    msg = "🛍️ **Select a Product to Buy:**\n\n"
    keyboard = []

    for key, pinfo in PRODUCTS.items():
      stk_len = len(data["stock"].get(key, []))
      btn_text = f"{pinfo['name']} - {pinfo['price']} RS ({stk_len} in stock)"
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
      msg = (
          f"📦 **Product Details:**\n\n"
          f"🔹 **Name:** {pinfo['name']}\n"
          f"💵 **Price (per item):** `{pinfo['price']} RS`\n"
          f"📊 **Available Stock:** `{stock_count} Available`\n\n"
          f"💰 **Aapka Balance:** `{user_info['balance']} RS`"
      )
      keyboard = [
          [
              InlineKeyboardButton(
                  "🛒 Buy Quantity", callback_data=f"buy_qty_{prod_key}"
              )
          ],
          [InlineKeyboardButton("🔙 Back to Store", callback_data="btn_store")],
      ]
      await query.message.edit_text(
          msg,
          reply_markup=InlineKeyboardMarkup(keyboard),
          parse_mode="Markdown",
      )

  elif query.data.startswith("buy_qty_"):
    prod_key = query.data.replace("buy_qty_", "")
    context.user_data["buying_prod"] = prod_key
    pinfo = PRODUCTS.get(prod_key)
    stock_count = len(data["stock"].get(prod_key, []))

    if stock_count == 0:
      await query.message.edit_text(
          f"❌ **Out of Stock!**\n\n`{pinfo['name']}` ka stock abhi khatam hai.",
          reply_markup=InlineKeyboardMarkup([[
              InlineKeyboardButton("🔙 Back to Store", callback_data="btn_store")
          ]]),
      )
      return

    await query.message.edit_text(
        f"🛒 **How many items do you want to buy?**\n\n"
        f"Product: `{pinfo['name']}`\n"
        f"Available Stock: `{stock_count}`\n"
        f"Price per item: `{pinfo['price']} RS`\n\n"
        f"⌨️ **Kitni quantity chahiye? (Number likhein jaise: 1, 2, 5):**"
    )

  elif query.data == "btn_wallet":
    msg = (
        f"💳 **Wallet Deposit Options**\n\n"
        f"💰 **Current Balance:** `{user_info['balance']} RS`\n\n"
        f"Payment method select karein:"
    )
    keyboard = [
        [
            InlineKeyboardButton(
                "📱 EasyPaisa / JazzCash", callback_data="dep_easypaisa"
            )
        ],
        [
            InlineKeyboardButton(
                "🟡 Binance (Pay ID / USDT)", callback_data="dep_binance"
            )
        ],
        [InlineKeyboardButton("🔙 Main Menu", callback_data="btn_main")],
    ]
    await query.message.edit_text(
        msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
    )

  elif query.data == "dep_easypaisa":
    msg = (
        f"📱 **EasyPaisa Deposit Details:**\n\n"
        f"📌 **Account Details:**\n"
        f"• **Number:** `{EASYPAISA_NO}`\n"
        f"• **Account Name:** {EASYPAISA_NAME}\n\n"
        f"💡 **Kaise Deposit Karein?**\n"
        f"1. Upar diye gaye number par payment send karein.\n"
        f"2. Niche **➕ Enter Custom Amount** click karke Amount aur TID enter"
        f" karein."
    )
    keyboard = [
        [
            InlineKeyboardButton(
                "➕ Enter Custom Amount", callback_data="start_dep_easypaisa"
            )
        ],
        [
            InlineKeyboardButton(
                "🔙 Back to Methods", callback_data="btn_wallet"
            )
        ],
    ]
    await query.message.edit_text(
        msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
    )

  elif query.data == "dep_binance":
    msg = (
        f"🟡 **Binance Pay Details:**\n\n"
        f"📌 **Account Details:**\n"
        f"• **Binance Pay ID:** `{BINANCE_PAY_ID}`\n"
        f"• **Account Name:** {BINANCE_NAME}\n\n"
        f"💡 **Kaise Deposit Karein?**\n"
        f"1. Pay ID par USDT send karein.\n"
        f"2. Niche **➕ Enter Custom Amount** click karke details submit"
        f" karein."
    )
    keyboard = [
        [
            InlineKeyboardButton(
                "➕ Enter Custom Amount", callback_data="start_dep_binance"
            )
        ],
        [
            InlineKeyboardButton(
                "🔙 Back to Methods", callback_data="btn_wallet"
            )
        ],
    ]
    await query.message.edit_text(
        msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
    )

  elif query.data == "btn_support":
    msg = (
        f"📞 **Customer Support / Help Desk**\n\n"
        f"Agar aapko koi problem aaye ya custom order dena ho, toh Admin se direct contact karein:\n\n"
        f"📱 **WhatsApp / Contact Number:** `{SUPPORT_CONTACT}`"
    )
    keyboard = [[InlineKeyboardButton("🔙 Main Menu", callback_data="btn_main")]]
    await query.message.edit_text(
        msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
    )

  elif query.data == "btn_main":
    await start(update, context)


# ================= Quantity Purchase Handler =================


async def receive_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
  user = update.effective_user
  user_id = str(user.id)
  text = update.message.text.strip()

  if not text.isdigit() or int(text) <= 0:
    await update.message.reply_text(
        "⚠️ Sahi number enter karein (e.g. 1, 2, 3):"
    )
    return WAITING_FOR_QTY

  qty = int(text)
  prod_key = context.user_data.get("buying_prod")
  pinfo = PRODUCTS.get(prod_key)

  data = load_data()
  stock = data["stock"].get(prod_key, [])
  user_balance = data["users"][user_id]["balance"]

  if qty > len(stock):
    await update.message.reply_text(
        f"❌ **Stock Kam Hai!**\nAvailable stock sirf `{len(stock)}` items hain."
        f" Aap kam quantity enter karein:",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Back to Store", callback_data="btn_store")
        ]]),
    )
    return ConversationHandler.END

  total_cost = pinfo["price"] * qty

  if user_balance < total_cost:
    await update.message.reply_text(
        f"⚠️ **Insufficient Balance!**\n\n"
        f"Total Price: `{total_cost} RS` | Aapka Balance:"
        f" `{user_balance} RS`\n\nPehle wallet deposit karein.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("💳 Deposit Money", callback_data="btn_wallet")
        ]]),
    )
    context.user_data.clear()
    return ConversationHandler.END

  bought_items = []
  for _ in range(qty):
    bought_items.append(stock.pop(0))

  data["users"][user_id]["balance"] -= total_cost
  data["stock"][prod_key] = stock
  save_data(data)

  items_str = "\n".join([f"{idx+1}: `{item}`" for idx, item in enumerate(bought_items)])

  await update.message.reply_text(
      f"🎉 **Purchase Successful!**\n\n"
      f"📦 **Product:** {pinfo['name']}\n"
      f"🔢 **Quantity:** `{qty}`\n"
      f"💰 **Total Deducted:** `{total_cost} RS`\n"
      f"💵 **Remaining Balance:** `{data['users'][user_id]['balance']} RS`\n\n"
      f"🔑 **Aapke Products:**\n{items_str}\n\n"
      f"Thank you for buying!",
      parse_mode="Markdown",
  )

  try:
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=(
            f"🛍️ **BULK ITEM SOLD!**\n\n"
            f"👤 **User:** {user.first_name} (`{user_id}`)\n"
            f"🔹 **Product:** {pinfo['name']}\n"
            f"🔢 **Quantity:** `{qty}`\n"
            f"💵 **Total Price:** `{total_cost} RS`\n"
            f"📦 **Remaining Stock:** `{len(stock)}`"
        ),
        parse_mode="Markdown",
    )
  except Exception:
    pass

  context.user_data.clear()
  return ConversationHandler.END


# ================= Custom Deposit Handler =================


async def start_custom_deposit(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
  query = update.callback_query
  await query.answer()
  if query.data == "start_dep_easypaisa":
    method = "EasyPaisa"
    curr_symbol = "RS"
  else:
    method = "Binance"
    curr_symbol = "$"

  context.user_data["dep_method"] = method
  context.user_data["curr_symbol"] = curr_symbol

  await query.message.reply_text(
      f"💵 **{method} Custom Deposit**\n\nAmount enter karein (e.g. 10"
      f" {curr_symbol}):"
  )
  return WAITING_FOR_AMOUNT


async def receive_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
  text = update.message.text.strip()
  if not text.isdigit() or int(text) <= 0:
    await update.message.reply_text("⚠️ Sahi numbers mein amount enter karein:")
    return WAITING_FOR_AMOUNT
  context.user_data["dep_amount"] = int(text)
  await update.message.reply_text(
      f"🧾 **Transaction Proof / TID**\n\nPayment TID bhejiyega:"
  )
  return WAITING_FOR_TID


async def receive_tid(update: Update, context: ContextTypes.DEFAULT_TYPE):
  user = update.effective_user
  user_id = str(user.id)
  tid = update.message.text.strip()
  amount = context.user_data.get("dep_amount", 0)
  method = context.user_data.get("dep_method", "Deposit")
  curr_symbol = context.user_data.get("curr_symbol", "RS")

  await update.message.reply_text(
      f"⏳ **Deposit Request Submitted!**\n\n"
      f"💳 **Method:** {method}\n"
      f"💰 **Amount:** `{amount} {curr_symbol}`\n"
      f"🧾 **TID:** `{tid}`\n\n"
      f"Admin verification ke baad add ho jayega.",
      parse_mode="Markdown",
  )

  admin_keyboard = [
      [
          InlineKeyboardButton(
              "✅ Approve", callback_data=f"app_{user_id}_{amount}_{curr_symbol}"
          ),
          InlineKeyboardButton("❌ Reject", callback_data=f"rej_{user_id}"),
      ]
  ]

  try:
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=(
            f"🔔 **NEW DEPOSIT NOTIFICATION!**\n\n"
            f"👤 **User:** {user.first_name} (@{user.username})\n"
            f"🆔 **User ID:** `{user_id}`\n"
            f"💳 **Method:** `{method.upper()}`\n"
            f"💰 **Amount:** `{amount} {curr_symbol}`\n"
            f"🧾 **TID:** `{tid}`"
        ),
        reply_markup=InlineKeyboardMarkup(admin_keyboard),
        parse_mode="Markdown",
    )
  except Exception as e:
    print(f"Error sending admin notification: {e}")

  context.user_data.clear()
  return ConversationHandler.END


async def cancel_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
  context.user_data.clear()
  await update.message.reply_text("❌ Cancelled.")
  return ConversationHandler.END


# ================= Admin Commands =================


async def add_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
  if update.effective_user.id != ADMIN_ID:
    return

  if not context.args:
    msg = "⚠️ **Syntax:** `/addstock [PRODUCT_KEY]`\n\n**Product Keys:**\n"
    for k in PRODUCTS:
      msg += f"• `{k}` ({PRODUCTS[k]['name']})\n"
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
        f"✅ **Stock Added Successfully!**\n\n"
        f"📦 Product: {PRODUCTS[prod_key]['name']}\n"
        f"➕ Added Items: `{len(lines)}`\n"
        f"📊 Total Stock: `{len(data['stock'][prod_key])} Available`",
        parse_mode="Markdown",
    )
  else:
    await update.message.reply_text(
        f"⚠️ Aapne product key `{prod_key}` likhi hai lekin items nahi diye.\n"
        f"Sahi tareeqa: `/addstock nordvpn 1:nordvpn.com:pass1`",
        parse_mode="Markdown",
    )


async def delete_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
  if update.effective_user.id != ADMIN_ID:
    return

  if len(context.args) < 2:
    msg = "⚠️ **Syntax:** `/delstock [PRODUCT_KEY] [INDEX]`\n\nExample: `/delstock gemini 0`"
    await update.message.reply_text(msg, parse_mode="Markdown")
    return

  prod_key = context.args[0].lower()
  try:
    index = int(context.args[1])
  except ValueError:
    await update.message.reply_text("❌ Index number hona chahiye (jaise: 0, 1, 2)")
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
      f"🗑️ **Stock Item Deleted Successfully!**\n\n"
      f"📦 **Product:** {PRODUCTS[prod_key]['name']}\n"
      f"❌ **Deleted Item:** `{removed_item}`\n"
      f"📊 **Remaining Stock:** `{len(stock_list)} Available`",
      parse_mode="Markdown",
  )


async def check_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
  if update.effective_user.id != ADMIN_ID:
    return

  data = load_data()
  msg = "📦 **Current Live Stock Summary & Numbered Items:**\n\n"
  for key, pinfo in PRODUCTS.items():
    stk_list = data["stock"].get(key, [])
    msg += f"🔹 **{pinfo['name']}** (`{key}`): `{len(stk_list)} Items`\n"
    for idx, item in enumerate(stk_list):
      msg += f"   {idx}: `{item}`\n"
    msg += "\n"

  await update.message.reply_text(msg, parse_mode="Markdown")


# ================= Admin Approval Callback =================


async def admin_approval_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
  query = update.callback_query
  await query.answer()
  if query.from_user.id != ADMIN_ID:
    return

  data_parts = query.data.split("_")
  action = data_parts[0]
  target_user_id = data_parts[1]
  data = load_data()

  if action == "app":
    amount = int(data_parts[2])
    curr_symbol = data_parts[3] if len(data_parts) > 3 else "RS"

    if target_user_id in data["users"]:
      data["users"][target_user_id]["balance"] += amount
      save_data(data)
      try:
        await context.bot.send_message(
            chat_id=int(target_user_id),
            text=(
                f"🎉 **Deposit Approved!**\n\n💰 `{amount} {curr_symbol}` added"
                " to wallet!"
            ),
            parse_mode="Markdown",
        )
      except Exception:
        pass
      await query.message.edit_text(
          f"{query.message.text}\n\n✅ **APPROVED (+{amount} {curr_symbol})**"
      )

  elif action == "rej":
    try:
      await context.bot.send_message(
          chat_id=int(target_user_id),
          text="❌ **Deposit Rejected!** Contact Admin.",
      )
    except Exception:
      pass
    await query.message.edit_text(f"{query.message.text}\n\n❌ **REJECTED**")


# ================= Main Function =================


def main():
  app = ApplicationBuilder().token(TOKEN).build()

  # Quantity Purchase Handler Conv
  qty_conv = ConversationHandler(
      entry_points=[CallbackQueryHandler(button_handler, pattern="^buy_qty_")],
      states={
          WAITING_FOR_QTY: [
              MessageHandler(filters.TEXT & ~filters.COMMAND, receive_quantity)
          ]
      },
      fallbacks=[CommandHandler("cancel", cancel_deposit)],
  )

  # Custom Deposit Handler Conv
  deposit_conv = ConversationHandler(
      entry_points=[
          CallbackQueryHandler(
              start_custom_deposit, pattern="^start_dep_(easypaisa|binance)$"
          )
      ],
      states={
          WAITING_FOR_AMOUNT: [
              MessageHandler(filters.TEXT & ~filters.COMMAND, receive_amount)
          ],
          WAITING_FOR_TID: [
              MessageHandler(filters.TEXT & ~filters.COMMAND, receive_tid)
          ],
      },
      fallbacks=[CommandHandler("cancel", cancel_deposit)],
  )

  app.add_handler(deposit_conv)
  app.add_handler(qty_conv)
  app.add_handler(CommandHandler("start", start))
  app.add_handler(CommandHandler("addstock", add_stock))
  app.add_handler(CommandHandler("delstock", delete_stock))
  app.add_handler(CommandHandler("stock", check_stock))
  app.add_handler(
      CallbackQueryHandler(admin_approval_callback, pattern="^(app|rej)_")
  )
  app.add_handler(CallbackQueryHandler(button_handler))

  print("Store Bot is Running Perfectly...")
  app.run_polling()


if __name__ == "__main__":
  main()