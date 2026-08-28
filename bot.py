"""
Telegram Shop Bot - លក់អាវ
============================
Bot សម្រាប់លក់អាវលើ Telegram៖ អតិថិជនអាចមើលទំនិញ ជ្រើសរើសទំហំ ដាក់ក្នុងកន្ត្រក
ហើយបញ្ជាទិញ។ ពេលបញ្ជាទិញរួច Bot នឹងផ្ញើសេចក្តីសង្ខេបទៅកាន់ Admin (អ្នកលក់)។

របៀបដំឡើង៖
1. pip install python-telegram-bot --upgrade
2. ដាក់ TOKEN ដែលបានពី @BotFather ក្នុងអថេរ BOT_TOKEN ខាងក្រោម
3. ដាក់ ADMIN_CHAT_ID (chat id របស់អ្នកលក់ ដែលទទួល order) - អាចដឹងបានដោយផ្ញើសារទៅ
   @userinfobot លើ Telegram
4. python bot.py
"""

import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ---------------- CONFIGURATION ----------------
BOT_TOKEN = "8503137382:AAEDE-pHtottu5gHet2HHjpH0OxIbHWqQZ0"  # ពី @BotFather
ADMIN_CHAT_ID = -5362036603                                     # chat id របស់អ្នកលក់

# ---------------- PRODUCT DATA ----------------
PRODUCTS = {
    "shirt1": {
        "name": "អាវយឺត Basic ពណ៌ស",
        "price": 8,
        "sizes": ["S", "M", "L", "XL"],
    },
    "shirt2": {
        "name": "អាវយឺត Oversize ខ្មៅ",
        "price": 10,
        "sizes": ["M", "L", "XL"],
    },
    "shirt3": {
        "name": "អាវពូឡូ Navy",
        "price": 12,
        "sizes": ["S", "M", "L"],
    },
    "shirt4": {
        "name": "អាវយឺត Graphic ក្រហម",
        "price": 9,
        "sizes": ["S", "M", "L", "XL"],
    },
}

logging.basicConfig(level=logging.INFO)

# cart ត្រូវបានរក្សាទុកជា user_data (per-chat memory ខណៈពេល bot កំពុងរត់)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.setdefault("cart", [])
    keyboard = [
        [InlineKeyboardButton(f"{p['name']} - ${p['price']}", callback_data=f"view_{pid}")]
        for pid, p in PRODUCTS.items()
    ]
    keyboard.append([InlineKeyboardButton("🛒 មើលកន្ត្រក", callback_data="cart")])
    await update.message.reply_text(
        "សូមស្វាគមន៍មកកាន់ហាងអាវយើង! ជ្រើសរើសទំនិញខាងក្រោម៖",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    context.user_data.setdefault("cart", [])

    if data.startswith("view_"):
        pid = data.split("_", 1)[1]
        product = PRODUCTS[pid]
        keyboard = [
            [InlineKeyboardButton(size, callback_data=f"add_{pid}_{size}") for size in product["sizes"]],
            [InlineKeyboardButton("⬅️ ត្រឡប់", callback_data="back")],
        ]
        await query.edit_message_text(
            f"{product['name']}\nតម្លៃ: ${product['price']}\nសូមជ្រើសរើសទំហំ៖",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif data.startswith("add_"):
        _, pid, size = data.split("_")
        product = PRODUCTS[pid]
        context.user_data["cart"].append({"name": product["name"], "price": product["price"], "size": size})
        await query.edit_message_text(
            f"✅ បានដាក់ {product['name']} (ទំហំ {size}) ចូលកន្ត្រកហើយ!\n\nវាយ /start ដើម្បីបន្តទិញ ឬ /cart ដើម្បីមើលកន្ត្រក។"
        )

    elif data == "cart":
        await show_cart(query, context)

    elif data == "back":
        await start_from_query(query, context)

    elif data == "checkout":
        await checkout(query, context)

    elif data == "clear":
        context.user_data["cart"] = []
        await query.edit_message_text("កន្ត្រកត្រូវបានសម្អាតរួចរាល់។ វាយ /start ដើម្បីទិញបន្ត។")


async def start_from_query(query, context):
    keyboard = [
        [InlineKeyboardButton(f"{p['name']} - ${p['price']}", callback_data=f"view_{pid}")]
        for pid, p in PRODUCTS.items()
    ]
    keyboard.append([InlineKeyboardButton("🛒 មើលកន្ត្រក", callback_data="cart")])
    await query.edit_message_text(
        "ជ្រើសរើសទំនិញខាងក្រោម៖", reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def show_cart(query, context):
    cart = context.user_data.get("cart", [])
    if not cart:
        await query.edit_message_text("កន្ត្រករបស់អ្នកទទេ។ វាយ /start ដើម្បីទិញ។")
        return
    total = sum(item["price"] for item in cart)
    lines = [f"- {item['name']} (ទំហំ {item['size']}) — ${item['price']}" for item in cart]
    text = "🛒 កន្ត្រករបស់អ្នក៖\n" + "\n".join(lines) + f"\n\nសរុប: ${total}"
    keyboard = [
        [InlineKeyboardButton("✅ បញ្ជាទិញ", callback_data="checkout")],
        [InlineKeyboardButton("🗑 សម្អាតកន្ត្រក", callback_data="clear")],
        [InlineKeyboardButton("⬅️ ត្រឡប់", callback_data="back")],
    ]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


async def checkout(query, context):
    cart = context.user_data.get("cart", [])
    if not cart:
        await query.edit_message_text("កន្ត្រករបស់អ្នកទទេ។")
        return
    context.user_data["awaiting_contact"] = True
    await query.edit_message_text(
        "សូមផ្ញើ ឈ្មោះ + លេខទូរស័ព្ទ + អាសយដ្ឋានដឹកជញ្ជូន របស់អ្នកជាសារមួយ ដើម្បីបញ្ចប់ការបញ្ជាទិញ។"
    )


async def contact_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("awaiting_contact"):
        return
    cart = context.user_data.get("cart", [])
    total = sum(item["price"] for item in cart)
    lines = [f"- {item['name']} (ទំហំ {item['size']}) — ${item['price']}" for item in cart]
    order_text = (
        f"🆕 ការបញ្ជាទិញថ្មី!\n"
        f"អតិថិជន: {update.effective_user.full_name} (@{update.effective_user.username})\n"
        f"ព័ត៌មានទំនាក់ទំនង: {update.message.text}\n\n"
        + "\n".join(lines)
        + f"\n\nសរុប: ${total}"
    )
    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=order_text)
    await update.message.reply_text("🎉 អរគុណសម្រាប់ការបញ្ជាទិញ! យើងខ្ញុំនឹងទាក់ទងអ្នកឆាប់ៗនេះ។")
    context.user_data["cart"] = []
    context.user_data["awaiting_contact"] = False


async def cart_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cart = context.user_data.get("cart", [])
    if not cart:
        await update.message.reply_text("កន្ត្រករបស់អ្នកទទេ។ វាយ /start ដើម្បីទិញ។")
        return
    total = sum(item["price"] for item in cart)
    lines = [f"- {item['name']} (ទំហំ {item['size']}) — ${item['price']}" for item in cart]
    text = "🛒 កន្ត្រករបស់អ្នក៖\n" + "\n".join(lines) + f"\n\nសរុប: ${total}"
    keyboard = [
        [InlineKeyboardButton("✅ បញ្ជាទិញ", callback_data="checkout")],
        [InlineKeyboardButton("🗑 សម្អាតកន្ត្រក", callback_data="clear")],
    ]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("cart", cart_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, contact_message_handler))
    print("Bot កំពុងរត់...")
    app.run_polling()


if __name__ == "__main__":
    main()
