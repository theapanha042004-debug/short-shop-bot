"""
ហាងអនឡាញ Telegram Bot
======================
Bot សម្រាប់លក់ទំនិញលើ Telegram - មានកន្ត្រកទំនិញ, ជ្រើសរើសការទូទាត់ (ABA/ACLEDA ឬ COD)

របៀបប្រើ:
1. ដំឡើង library:  pip install python-telegram-bot --upgrade
2. ដាក់ BOT_TOKEN និង ADMIN_CHAT_ID ខាងក្រោម
3. កែប្រែបញ្ជីទំនិញនៅផ្នែក PRODUCTS
4. រត់ដោយ:  python bot.py
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ConversationHandler, ContextTypes, filters
)

logging.basicConfig(level=logging.INFO)

# ========== ការកំណត់ (ត្រូវកែ) ==========
BOT_TOKEN = "8567152645:AAGrkdg4Eka5aaqCbLZal6UOQGgKAA2FXBQ"       # យកពី @BotFather
ADMIN_CHAT_ID =-5362036603               # Chat ID របស់អ្នកគ្រប់គ្រងហាង (ទទួលការបញ្ជាទិញ)

PAYMENT_INFO = {
    "aba": "លេខគណនី ABA: 000 000 000\nឈ្មោះ: [ឈ្មោះអ្នក]",
    "acleda": "លេខគណនី ACLEDA: 0000 0000 0000\nឈ្មោះ: [ឈ្មោះអ្នក]",
}

# ========== បញ្ជីទំនិញ (ត្រូវកែតាមហាងអ្នក) ==========
PRODUCTS = {
    "clothes": {
        "name": "👕 សម្លៀកបំពាក់",
        "items": [
            {"id": "c1", "name": "អាវយឺត", "price": 15},
            {"id": "c2", "name": "ខោខូវប៊យ", "price": 25},
        ],
    },
    "food": {
        "name": "🍜 អាហារ/ភេសជ្ជៈ",
        "items": [
            {"id": "f1", "name": "នំបុ័ង", "price": 3},
            {"id": "f2", "name": "កាហ្វេ", "price": 2},
        ],
    },
    "electronics": {
        "name": "🔌 គ្រឿងអេឡិចត្រូនិក",
        "items": [
            {"id": "e1", "name": "ខ្សែសាកថ្ម", "price": 5},
            {"id": "e2", "name": "កាសស្តាប់", "price": 12},
        ],
    },
}

def find_item(item_id):
    for cat in PRODUCTS.values():
        for it in cat["items"]:
            if it["id"] == item_id:
                return it
    return None

# ========== ស្ថានភាព Conversation សម្រាប់ Checkout ==========
ASK_PAYMENT, ASK_ADDRESS = range(2)

# ========== Handlers ==========

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.setdefault("cart", {})
    keyboard = [[InlineKeyboardButton(cat["name"], callback_data=f"cat_{key}")]
                for key, cat in PRODUCTS.items()]
    keyboard.append([InlineKeyboardButton("🛒 មើលកន្ត្រក", callback_data="view_cart")])
    await update.message.reply_text(
        "សូមស្វាគមន៍មកកាន់ហាងអនឡាញ! 🛍️\nជ្រើសរើសប្រភេទទំនិញ៖",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    cat_key = query.data.replace("cat_", "")
    cat = PRODUCTS[cat_key]
    keyboard = [
        [InlineKeyboardButton(f"{it['name']} - ${it['price']}", callback_data=f"add_{it['id']}")]
        for it in cat["items"]
    ]
    keyboard.append([InlineKeyboardButton("⬅️ ត្រឡប់", callback_data="back_main")])
    await query.edit_message_text(f"{cat['name']}\nជ្រើសរើសទំនិញដើម្បីបញ្ចូលកន្ត្រក៖",
                                   reply_markup=InlineKeyboardMarkup(keyboard))

async def add_to_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    item_id = query.data.replace("add_", "")
    item = find_item(item_id)
    cart = context.user_data.setdefault("cart", {})
    cart[item_id] = cart.get(item_id, 0) + 1
    await query.answer(f"✅ បានបញ្ចូល {item['name']} ចូលកន្ត្រក")

async def view_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    cart = context.user_data.get("cart", {})
    if not cart:
        await query.edit_message_text("កន្ត្រកទទេ។ សូមជ្រើសរើសទំនិញសិន។",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ ត្រឡប់", callback_data="back_main")]]))
        return
    lines, total = [], 0
    for item_id, qty in cart.items():
        it = find_item(item_id)
        subtotal = it["price"] * qty
        total += subtotal
        lines.append(f"{it['name']} x{qty} = ${subtotal}")
    text = "🛒 កន្ត្រករបស់អ្នក៖\n\n" + "\n".join(lines) + f"\n\nសរុប: ${total}"
    keyboard = [
        [InlineKeyboardButton("✅ បញ្ជាទិញ", callback_data="checkout")],
        [InlineKeyboardButton("⬅️ ត្រឡប់", callback_data="back_main")],
    ]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def back_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [[InlineKeyboardButton(cat["name"], callback_data=f"cat_{key}")]
                for key, cat in PRODUCTS.items()]
    keyboard.append([InlineKeyboardButton("🛒 មើលកន្ត្រក", callback_data="view_cart")])
    await query.edit_message_text("ជ្រើសរើសប្រភេទទំនិញ៖", reply_markup=InlineKeyboardMarkup(keyboard))

# ---- Checkout flow ----

async def checkout_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("ABA", callback_data="pay_aba")],
        [InlineKeyboardButton("ACLEDA", callback_data="pay_acleda")],
        [InlineKeyboardButton("COD (បង់ពេលទទួល)", callback_data="pay_cod")],
    ]
    await query.edit_message_text("សូមជ្រើសរើសវិធីទូទាត់៖", reply_markup=InlineKeyboardMarkup(keyboard))
    return ASK_PAYMENT

async def ask_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    method = query.data.replace("pay_", "")
    context.user_data["payment_method"] = method
    if method in PAYMENT_INFO:
        await query.edit_message_text(
            f"ព័ត៌មានទូទាត់៖\n{PAYMENT_INFO[method]}\n\nសូមផ្ទេរប្រាក់ រួចផ្ញើអាសយដ្ឋានដឹកជញ្ជូនរបស់អ្នកមកខាងក្រោម៖"
        )
    else:
        await query.edit_message_text("សូមផ្ញើអាសយដ្ឋានដឹកជញ្ជូនរបស់អ្នក៖")
    return ASK_ADDRESS

async def confirm_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    address = update.message.text
    cart = context.user_data.get("cart", {})
    method = context.user_data.get("payment_method", "?")
    lines, total = [], 0
    for item_id, qty in cart.items():
        it = find_item(item_id)
        subtotal = it["price"] * qty
        total += subtotal
        lines.append(f"{it['name']} x{qty} = ${subtotal}")
    order_text = (
        f"🆕 ការបញ្ជាទិញថ្មី!\n\n"
        f"👤 អតិថិជន: {update.effective_user.full_name} (@{update.effective_user.username})\n"
        f"📦 ទំនិញ:\n" + "\n".join(lines) +
        f"\n💰 សរុប: ${total}\n💳 ការទូទាត់: {method}\n📍 អាសយដ្ឋាន: {address}"
    )
    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=order_text)
    await update.message.reply_text("🎉 អរគុណ! ការបញ្ជាទិញរបស់អ្នកត្រូវបានទទួល។ យើងខ្ញុំនឹងទាក់ទងអ្នកឆាប់ៗនេះ។")
    context.user_data["cart"] = {}
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("បានបោះបង់ការបញ្ជាទិញ។ វាយ /start ដើម្បីចាប់ផ្តើមម្តងទៀត។")
    return ConversationHandler.END

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    checkout_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(checkout_start, pattern="^checkout$")],
        states={
            ASK_PAYMENT: [CallbackQueryHandler(ask_address, pattern="^pay_")],
            ASK_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_order)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(checkout_conv)
    app.add_handler(CallbackQueryHandler(show_category, pattern="^cat_"))
    app.add_handler(CallbackQueryHandler(add_to_cart, pattern="^add_"))
    app.add_handler(CallbackQueryHandler(view_cart, pattern="^view_cart$"))
    app.add_handler(CallbackQueryHandler(back_main, pattern="^back_main$"))

    print("Bot កំពុងដំណើរការ...")
    app.run_polling()

if __name__ == "__main__":
    main()
