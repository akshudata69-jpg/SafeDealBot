# ================= SAFEDEAL BOT FINAL (GITHUB VERSION) =================

import sqlite3
from datetime import datetime
import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# ---------------- CONFIG ----------------
TOKEN = os.getenv("TOKEN")
CHANNEL = "@AksharStore"
OWNER_USERNAME = "@KING_HU_MAI"
ADMIN_ID = 1804489867  # your telegram ID

# ---------------- DATABASE ----------------
conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    reports INTEGER DEFAULT 0,
    proofs INTEGER DEFAULT 0,
    approved INTEGER DEFAULT 0
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS reports (
    reporter_id INTEGER,
    username TEXT,
    date TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS banned (
    user_id INTEGER PRIMARY KEY
)
""")

conn.commit()

# ---------------- MENU ----------------
menu = ReplyKeyboardMarkup(
    [
        ["🔍 Check Seller", "🚨 Report Seller"],
        ["📸 Submit Proof", "🏆 Top Trusted"],
        ["ℹ️ Help"]
    ],
    resize_keyboard=True
)

# ---------------- FORCE JOIN ----------------
async def force_join(update, context):
    user_id = update.effective_user.id
    member = await context.bot.get_chat_member(CHANNEL, user_id)

    if member.status not in ["member", "administrator", "creator"]:
        await update.message.reply_text(f"🔒 Join channel first:\n{CHANNEL}")
        return False
    return True

# ---------------- TRUST SCORE ----------------
def calculate_score(reports, approved):
    score = 50 + (approved * 10) - (reports * 15)
    return max(0, min(100, score))

# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await force_join(update, context):
        return

    await update.message.reply_text(
        "🚨 Welcome to SafeDeal Bot\n\nChoose option 👇",
        reply_markup=menu
    )

# ---------------- BUTTON HANDLER ----------------
async def buttons(update, context):
    if not await force_join(update, context):
        return

    text = update.message.text

    if text == "🔍 Check Seller":
        context.user_data["mode"] = "check"
        await update.message.reply_text("Send seller username (@user)")

    elif text == "🚨 Report Seller":
        context.user_data["mode"] = "report"
        await update.message.reply_text("Send username to report")

    elif text == "📸 Submit Proof":
        context.user_data["mode"] = "proof_user"
        await update.message.reply_text("Send your username")

    elif text == "🏆 Top Trusted":
        cursor.execute("SELECT username, approved FROM users ORDER BY approved DESC LIMIT 5")
        data = cursor.fetchall()

        if not data:
            await update.message.reply_text("No trusted sellers yet.")
            return

        msg = "🏆 Top Trusted Sellers:\n\n"
        for i, row in enumerate(data, 1):
            msg += f"{i}. {row[0]} (Proofs: {row[1]})\n"

        await update.message.reply_text(msg)

    elif text == "ℹ️ Help":
        await update.message.reply_text(
            "Use this bot to check scams.\nNo Proof = No Deal ⚠️"
        )

# ---------------- TEXT HANDLER ----------------
async def handle_text(update, context):
    if not await force_join(update, context):
        return

    text = update.message.text.lower()
    mode = context.user_data.get("mode")

    # CHECK SELLER
    if mode == "check":
        cursor.execute("SELECT * FROM users WHERE username=?", (text,))
        data = cursor.fetchone()

        if not data:
            await update.message.reply_text(
                f"⚠️ No data found\n\n📩 Contact: {OWNER_USERNAME}\n\n(No Proof = No Deal ⚠️)"
            )
            return

        reports, proofs, approved = data[1], data[2], data[3]
        score = calculate_score(reports, approved)

        await update.message.reply_text(
            f"👤 Seller: {text}\n"
            f"🚨 Reports: {reports}\n"
            f"✅ Approved Proofs: {approved}\n"
            f"⭐ Trust Score: {score}%\n\n"
            "Always verify before dealing."
        )

    # REPORT SYSTEM
    elif mode == "report":
        user_id = update.effective_user.id
        today = datetime.now().strftime("%Y-%m-%d")

        cursor.execute("SELECT COUNT(*) FROM reports WHERE reporter_id=? AND date=?", (user_id, today))
        if cursor.fetchone()[0] >= 3:
            await update.message.reply_text("⚠️ Daily report limit reached.")
            return

        cursor.execute("SELECT * FROM reports WHERE reporter_id=? AND username=?", (user_id, text))
        if cursor.fetchone():
            await update.message.reply_text("⚠️ You already reported this seller.")
            return

        cursor.execute("INSERT INTO reports VALUES (?,?,?)", (user_id, text, today))

        cursor.execute("SELECT * FROM users WHERE username=?", (text,))
        if cursor.fetchone():
            cursor.execute("UPDATE users SET reports = reports + 1 WHERE username=?", (text,))
        else:
            cursor.execute("INSERT INTO users (username, reports) VALUES (?,1)", (text,))

        conn.commit()

        context.user_data["reporting"] = text
        await update.message.reply_text("🚨 Report added. Now send proof screenshot 📸")

    # SELLER PROOF SUBMISSION
    elif mode == "proof_user":
        context.user_data["proof_user"] = text
        context.user_data["mode"] = "waiting_proof"
        await update.message.reply_text("Send proof screenshot 📸")

# ---------------- PHOTO HANDLER ----------------
async def handle_photo(update, context):
    if context.user_data.get("mode") != "waiting_proof":
        return

    username = context.user_data["proof_user"]

    await context.bot.send_photo(
        chat_id=ADMIN_ID,
        photo=update.message.photo[-1].file_id,
        caption=f"📸 Proof for {username}\n\n/approve {username}\n/reject {username}"
    )

    await update.message.reply_text("✅ Proof sent for admin approval.")

    context.user_data.clear()

# ---------------- ADMIN COMMANDS ----------------
async def approve(update, context):
    if update.effective_user.id != ADMIN_ID:
        return

    username = context.args[0].lower()

    cursor.execute("UPDATE users SET approved = approved + 1 WHERE username=?", (username,))
    conn.commit()

    await update.message.reply_text(f"✅ Approved proof for {username}")

async def reject(update, context):
    if update.effective_user.id != ADMIN_ID:
        return

    await update.message.reply_text("❌ Proof rejected")

async def ban(update, context):
    if update.effective_user.id != ADMIN_ID:
        return

    user_id = int(context.args[0])

    cursor.execute("INSERT INTO banned VALUES (?)", (user_id,))
    conn.commit()

    await update.message.reply_text("🚫 User banned")

# ---------------- RUN ----------------
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("approve", approve))
app.add_handler(CommandHandler("reject", reject))
app.add_handler(CommandHandler("ban", ban))

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, buttons))
app.add_handler(MessageHandler(filters.TEXT, handle_text))
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

print("Bot is running...")
app.run_polling()
