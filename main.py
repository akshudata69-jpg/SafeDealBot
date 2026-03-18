import os
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

# ================= CONFIG =================
TOKEN = os.getenv("TOKEN")
CHANNEL_USERNAME = "@AKSHARSTORE"
ADMIN_ID = 1804489867

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

# ================= JOIN CHECK =================
async def is_joined(user_id, context):
    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if not await is_joined(user.id, context):
        keyboard = [[InlineKeyboardButton("Join Channel", url="https://t.me/AKSHARSTORE")]]
        await update.message.reply_text(
            "❌ Join channel first to use bot",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    keyboard = [
        [InlineKeyboardButton("🔍 Check Seller", callback_data="check")],
        [InlineKeyboardButton("🚨 Report Seller", callback_data="report")],
        [InlineKeyboardButton("📂 Seller Profile", callback_data="profile")],
        [InlineKeyboardButton("📤 Submit Proof", callback_data="proof")]
    ]

    await update.message.reply_text("🔥 SafeDeal Bot Ready", reply_markup=InlineKeyboardMarkup(keyboard))

# ================= BUTTONS =================
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "check":
        context.user_data["mode"] = "check"
        await query.message.reply_text("Send seller username:")

    elif query.data == "report":
        context.user_data["mode"] = "report"
        await query.message.reply_text("Send seller username to report:")

    elif query.data == "profile":
        context.user_data["mode"] = "profile"
        await query.message.reply_text("Send seller username:")

    elif query.data == "proof":
        context.user_data["mode"] = "proof"
        await query.message.reply_text("Send seller username:")

# ================= MESSAGE HANDLER =================
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
        status = "✅ SAFE" if score > 60 else "⚠️ RISKY" if score > 30 else "❌ SCAMMER"

        await update.message.reply_text(
            f"Seller: {seller}\nTrust Score: {score}%\nReports: {r}\nProofs: {p}\nStatus: {status}"
        )

    elif mode == "report":
        data[seller]["reports"] += 1
        await update.message.reply_text("🚨 Report added")

    elif mode == "profile":
        r = data[seller]["reports"]
        p = data[seller]["proofs"]

        await update.message.reply_text(
            f"📂 Seller Profile\n\nSeller: {seller}\nReports: {r}\nProofs: {p}"
        )

    elif mode == "proof":
        # Send proof request to admin
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"📩 New proof request for: {seller}\n\nUse:\n/approve {seller}\n/reject {seller}"
        )
        await update.message.reply_text("📤 Proof sent for admin approval")

    save_data(data)

# ================= ADMIN COMMANDS =================
async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    seller = context.args[0].lower()
    data = load_data()

    if seller not in data:
        data[seller] = {"reports": 0, "proofs": 0}

    data[seller]["proofs"] += 1
    save_data(data)

    await update.message.reply_text(f"✅ Approved proof for {seller}")

async def reject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    await update.message.reply_text("❌ Proof rejected")

async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
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
app.add_handler(CommandHandler("reject", reject))
app.add_handler(CommandHandler("ban", ban))
app.add_handler(CommandHandler("stats", stats))

print("Bot is running...")
app.run_polling()
