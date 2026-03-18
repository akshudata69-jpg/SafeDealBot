import os
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

# ================= CONFIG =================
TOKEN = os.getenv("TOKEN")
ADMIN_ID = 1804489867
CHANNEL = "@AKSHARSTORE"

DATA_FILE = "data.json"

# ================= DATA =================
def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🔍 Check Seller", callback_data="check")],
        [InlineKeyboardButton("🚨 Report Seller", callback_data="report")],
        [InlineKeyboardButton("📂 Seller Profile", callback_data="profile")],
        [InlineKeyboardButton("📤 Submit Proof", callback_data="proof")]
    ]

    await update.message.reply_text(
        "🔥 Welcome to SafeDeal Bot\n\nCheck sellers, avoid scams, stay safe.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ================= BUTTON =================
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    context.user_data["mode"] = query.data

    if query.data == "proof":
        await query.message.reply_text("Send seller username for proof submission:")
    else:
        await query.message.reply_text("Send seller username:")

# ================= MAIN HANDLER =================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode = context.user_data.get("mode")
    seller = update.message.text.lower()

    data = load_data()

    if seller not in data:
        data[seller] = {"reports": 0, "proofs": 0}

    if mode == "check":
        r = data[seller]["reports"]
        p = data[seller]["proofs"]

        score = max(0, 100 - r20 + p10)

        if score > 60:
            status = "✅ SAFE"
        elif score > 30:
            status = "⚠️ RISKY"
        else:
            status = "❌ SCAMMER"

        await update.message.reply_text(
            f"🔍 Seller: {seller}\n\n⭐ Trust Score: {score}%\n🚨 Reports: {r}\n📂 Proofs: {p}\n\nStatus: {status}"
        )

    elif mode == "report":
        data[seller]["reports"] += 1
        await update.message.reply_text("🚨 Report added successfully")

    elif mode == "profile":
        r = data[seller]["reports"]
        p = data[seller]["proofs"]

        await update.message.reply_text(
            f"📂 Seller Profile\n\n👤 Seller: {seller}\n🚨 Reports: {r}\n📤 Proofs: {p}"
        )

    elif mode == "proof":
        # Send request to admin
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"📩 New proof request\n\nSeller: {seller}\n\nUse:\n/approve {seller}\n/ban {seller}"
        )

        await update.message.reply_text("📤 Proof sent to admin for approval")

    save_data(data)

# ================= ADMIN =================
async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text("Usage: /approve username")
        return

    seller = context.args[0].lower()
    data = load_data()

    if seller not in data:
        data[seller] = {"reports": 0, "proofs": 0}

    data[seller]["proofs"] += 1
    save_data(data)

    await update.message.reply_text(f"✅ Approved proof for {seller}")

async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text("Usage: /ban username")
        return

    seller = context.args[0].lower()
    data = load_data()

    if seller not in data:
        data[seller] = {"reports": 0, "proofs": 0}

    data[seller]["reports"] += 5
    save_data(data)

    await update.message.reply_text(f"🚫 {seller} marked as scammer")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    data = load_data()
    await update.message.reply_text(f"📊 Total sellers: {len(data)}")

# ================= RUN =================
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

app.add_handler(CommandHandler("approve", approve))
app.add_handler(CommandHandler("ban", ban))
app.add_handler(CommandHandler("stats", stats))

print("Bot running...")
app.run_polling()
