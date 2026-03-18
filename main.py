import os
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

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

# ================= JOIN CHECK =================
async def is_joined(user_id, context):
    try:
        member = await context.bot.get_chat_member(CHANNEL, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_joined(update.effective_user.id, context):
        keyboard = [[InlineKeyboardButton("Join Channel", url="https://t.me/AKSHARSTORE")]]
        await update.message.reply_text("❌ Join channel first", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    keyboard = [
        [InlineKeyboardButton("🔍 Check Seller", callback_data="check")],
        [InlineKeyboardButton("🚨 Report Seller", callback_data="report")],
        [InlineKeyboardButton("📂 Profile", callback_data="profile")],
        [InlineKeyboardButton("📤 Submit Proof", callback_data="proof")],
        [InlineKeyboardButton("🏆 Top Sellers", callback_data="top")],
        [InlineKeyboardButton("🚫 Scammer List", callback_data="scammers")]
    ]

    await update.message.reply_text("🔥 SafeDeal PRO Bot", reply_markup=InlineKeyboardMarkup(keyboard))

# ================= BUTTON =================
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    context.user_data["mode"] = query.data

    if query.data in ["check", "report", "profile", "proof"]:
        await query.message.reply_text("Send seller username:")

    elif query.data == "top":
        data = load_data()
        sorted_data = sorted(data.items(), key=lambda x: x[1]["proofs"], reverse=True)

        msg = "🏆 Top Sellers:\n\n"
        for i, (k, v) in enumerate(sorted_data[:5], 1):
            msg += f"{i}. {k} ({v['proofs']} proofs)\n"

        await query.message.reply_text(msg)

    elif query.data == "scammers":
        data = load_data()
        msg = "🚫 Scammers:\n\n"

        for k, v in data.items():
            if v["reports"] >= 3:
                msg += f"{k} ({v['reports']} reports)\n"

        await query.message.reply_text(msg if msg != "🚫 Scammers:\n\n" else "No scammers yet")

# ================= TEXT =================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode = context.user_data.get("mode")
    seller = update.message.text.lower()

    data = load_data()

    if seller not in data:
        data[seller] = {"reports": 0, "proofs": 0, "verified": False}

    if mode == "check":
        r = data[seller]["reports"]
        p = data[seller]["proofs"]

        score = max(0, 100 - r25 + p15)

        badge = "👑 VERIFIED" if data[seller]["verified"] else ""

        status = "✅ SAFE" if score > 60 else "⚠️ RISKY" if score > 30 else "❌ SCAMMER"

        await update.message.reply_text(
            f"Seller: {seller}\n{badge}\nScore: {score}%\nReports: {r}\nProofs: {p}\nStatus: {status}"
        )

    elif mode == "report":
        data[seller]["reports"] += 1
        await update.message.reply_text("🚨 Report added")

    elif mode == "profile":
        r = data[seller]["reports"]
        p = data[seller]["proofs"]

        await update.message.reply_text(
            f"📂 Profile\nSeller: {seller}\nReports: {r}\nProofs: {p}"
        )

    elif mode == "proof":
        context.user_data["proof_seller"] = seller
        await update.message.reply_text("Send proof image 📸")

    save_data(data)

# ================= PHOTO =================
async def photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    seller = context.user_data.get("proof_seller")

    if not seller:
        return

    photo_file = update.message.photo[-1].file_id

    keyboard = [[
        InlineKeyboardButton("✅ Approve", callback_data=f"approve_{seller}"),
        InlineKeyboardButton("❌ Reject", callback_data=f"reject_{seller}")
    ]]

    await context.bot.send_photo(
        chat_id=ADMIN_ID,
        photo=photo_file,
        caption=f"Proof for {seller}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    await update.message.reply_text("📤 Sent to admin")

# ================= ADMIN BUTTON =================
async def admin_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = load_data()

    action, seller = query.data.split("")

    if action == "approve":
        data[seller]["proofs"] += 1
        await query.message.reply_text(f"✅ Approved {seller}")

    elif action == "reject":
        await query.message.reply_text("❌ Rejected")

    save_data(data)

# ================= ADMIN =================
async def verify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    seller = context.args[0].lower()
    data = load_data()

    data[seller]["verified"] = True
    save_data(data)

    await update.message.reply_text(f"👑 {seller} verified")

# ================= RUN =================
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button))
app.add_handler(CallbackQueryHandler(admin_button, pattern="^(approve|reject)"))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
app.add_handler(MessageHandler(filters.PHOTO, photo))

app.add_handler(CommandHandler("verify", verify))

print("PRO Bot running...")
app.run_polling(
