import re
from telegram import Update, BotCommand
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# =========================
# TOKEN BOT
# =========================
TOKEN = "8641291429:AAFWEDwH8TywfJaezJVKTWDp1HZsCvOCVI8"

# =========================
# OWNER & USER MANAGEMENT
# =========================
OWNER_USERNAME = "kannxyz14"  # hanya ini yang bisa add/remove user
allowed_users = set()          # user yang diizinkan pakai bot

# =========================
# DATA USER (LIST TERKIRIM)
# =========================
data_user = {}

# =========================
# CEK USER DIIZINKAN
# =========================
def is_allowed(update):
    username = update.message.from_user.username
    if not username:
        return False
    return username.lower() in allowed_users or username.lower() == OWNER_USERNAME

# =========================
# HITUNG FEE
# =========================
def hitung_fee(saldo):
    return (saldo // 10) + 1

# =========================
# PARSE LIST (LF, EMOJI, NAMA PANJANG)
# =========================
def parse_list(text):
    data = []
    for line in text.split("\n"):
        line = line.strip()
        if not line or ":" in line:
            continue
        match = re.search(r'(\d+)\s*(LF)?$', line, re.IGNORECASE)
        if match:
            saldo = int(match.group(1))
            lf = bool(match.group(2))
            nama = line[:match.start()].strip()
            if not nama:
                nama = "PLAYER"
            data.append((nama, saldo, lf))
    return data

# =========================
# SIMPAN LIST
# =========================
async def simpan_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        return  # abaikan chat user tidak diizinkan

    user_id = update.message.from_user.id
    text = update.message.text.strip()

    baris = [b for b in re.split(r'\n\s*\n', text) if b.strip()]
    if not text or ":" not in text or len(baris) < 2:
        return  # abaikan chat lain

    data_user[user_id] = text
    await update.message.reply_text("List disimpan ✅")

# =========================
# REKAP
# =========================
async def rekap(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        return

    user_id = update.message.from_user.id
    if update.message.reply_to_message and update.message.reply_to_message.text:
        text = update.message.reply_to_message.text
    elif user_id in data_user:
        text = data_user[user_id]
    else:
        await update.message.reply_text("Kirim list dulu atau reply ke list.")
        return

    bagian = [b.strip() for b in re.split(r'\n\s*\n', text) if b.strip()]
    if len(bagian) < 2:
        await update.message.reply_text("List harus berisi 2 tim.")
        return

    tim1_text, tim2_text = bagian[0], bagian[1]
    nama_tim1 = tim1_text.split("\n")[0].replace(":", "").strip()
    nama_tim2 = tim2_text.split("\n")[0].replace(":", "").strip()
    tim1 = parse_list(tim1_text)
    tim2 = parse_list(tim2_text)

    total1 = sum(x[1] for x in tim1)
    total2 = sum(x[1] for x in tim2)
    selisih = abs(total1 - total2)

    if total1 > total2:
        hasil = f"{nama_tim2} KEKURANGAN {selisih}K UNTUK MENYAMAI {nama_tim1}"
    elif total2 > total1:
        hasil = f"{nama_tim1} KEKURANGAN {selisih}K UNTUK MENYAMAI {nama_tim2}"
    else:
        hasil = "SALDO SUDAH SEIMBANG"

    msg = f"""
TOTAL {nama_tim1} : {total1}K
TOTAL {nama_tim2} : {total2}K

SELISIH : {selisih}K
{hasil}
"""
    await update.message.reply_text(msg)

# =========================
# REKAP WIN
# =========================
async def rekap_win(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        return

    user_id = update.message.from_user.id
    if update.message.reply_to_message and update.message.reply_to_message.text:
        text = update.message.reply_to_message.text
    elif user_id in data_user:
        text = data_user[user_id]
    else:
        await update.message.reply_text("Kirim list dulu atau reply ke list.")
        return

    bagian = [b.strip() for b in re.split(r'\n\s*\n', text) if b.strip()]
    if len(bagian) < 2:
        await update.message.reply_text("List harus berisi 2 tim.")
        return

    tim1_text, tim2_text = bagian[0], bagian[1]
    nama_tim1 = tim1_text.split("\n")[0].replace(":", "").strip()
    nama_tim2 = tim2_text.split("\n")[0].replace(":", "").strip()
    tim1 = parse_list(tim1_text)
    tim2 = parse_list(tim2_text)

    hasil = ""
    total_fee = 0

    # TIM 1
    hasil += f"{nama_tim1}:\n"
    for nama, saldo, lf in tim1:
        fee = hitung_fee(saldo)
        if lf:
            terima = saldo - fee
        else:
            terima = (saldo * 2) - fee
        total_fee += fee
        hasil += f"{nama} {saldo}//{terima}\n"

    hasil += "\n"

    # TIM 2
    hasil += f"{nama_tim2}:\n"
    for nama, saldo, lf in tim2:
        fee = hitung_fee(saldo)
        if lf:
            terima = saldo - fee
        else:
            terima = (saldo * 2) - fee
        total_fee += fee
        hasil += f"{nama} {saldo}//{terima}\n"

    hasil += f"\nTOTAL FEE YANG ANDA DAPAT = {total_fee}K"
    await update.message.reply_text(hasil)

# =========================
# REFUND
# =========================
async def refund(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        return

    user_id = update.message.from_user.id
    if update.message.reply_to_message and update.message.reply_to_message.text:
        text = update.message.reply_to_message.text
    elif user_id in data_user:
        text = data_user[user_id]
    else:
        await update.message.reply_text("Kirim list dulu atau reply ke list.")
        return

    bagian = [b.strip() for b in re.split(r'\n\s*\n', text) if b.strip()]
    if len(bagian) < 2:
        await update.message.reply_text("List harus berisi 2 tim.")
        return

    tim1_text, tim2_text = bagian[0], bagian[1]
    nama_tim1 = tim1_text.split("\n")[0].replace(":", "").strip()
    nama_tim2 = tim2_text.split("\n")[0].replace(":", "").strip()
    tim1 = parse_list(tim1_text)
    tim2 = parse_list(tim2_text)

    hasil = ""
    total_fee = 0

    # TIM 1
    hasil += f"{nama_tim1}:\n"
    for nama, saldo, lf in tim1:
        fee = hitung_fee(saldo)
        kembali = saldo - fee
        total_fee += fee
        hasil += f"{nama} {saldo}//{kembali}\n"

    hasil += "\n"

    # TIM 2
    hasil += f"{nama_tim2}:\n"
    for nama, saldo, lf in tim2:
        fee = hitung_fee(saldo)
        kembali = saldo - fee
        total_fee += fee
        hasil += f"{nama} {saldo}//{kembali}\n"

    hasil += f"\nTOTAL FEE YANG ANDA DAPAT = {total_fee}K"
    await update.message.reply_text(hasil)

# =========================
# START
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update):
        return
    await update.message.reply_text(
        "Kirim list taruhan dulu.\n\n"
        "Lalu gunakan:\n"
        "/rekap\n"
        "/rekap_win\n"
        "/refund\n"
        "Owner bisa menambah/hapus user: /adduser /removeuser"
    )

# =========================
# ADD / REMOVE USER (OWNER ONLY)
# =========================
async def adduser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.username.lower() != OWNER_USERNAME:
        await update.message.reply_text("Hanya owner yang bisa menambahkan user.")
        return
    if not context.args:
        await update.message.reply_text("Gunakan: /adduser username1 username2 ...")
        return
    added = []
    for user in context.args:
        u = user.lower().replace("@", "")
        allowed_users.add(u)
        added.append(u)
    await update.message.reply_text(f"User berhasil ditambahkan: {', '.join(added)}")

async def removeuser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.username.lower() != OWNER_USERNAME:
        await update.message.reply_text("Hanya owner yang bisa menghapus user.")
        return
    if not context.args:
        await update.message.reply_text("Gunakan: /removeuser username1 username2 ...")
        return
    removed = []
    for user in context.args:
        u = user.lower().replace("@", "")
        if u in allowed_users:
            allowed_users.remove(u)
            removed.append(u)
    await update.message.reply_text(f"User berhasil dihapus: {', '.join(removed)}")

# =========================
# SET COMMAND MENU
# =========================
async def set_commands(app):
    await app.bot.set_my_commands([
        BotCommand("start", "Mulai bot"),
        BotCommand("rekap", "Rekap selisih tim"),
        BotCommand("rekap_win", "Rekap kemenangan"),
        BotCommand("refund", "Refund saldo"),
        BotCommand("adduser", "Owner: Tambah user"),
        BotCommand("removeuser", "Owner: Hapus user")
    ])

# =========================
# JALANKAN BOT
# =========================
app = ApplicationBuilder().token(TOKEN).build()

# handler command
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("rekap", rekap))
app.add_handler(CommandHandler("rekap_win", rekap_win))
app.add_handler(CommandHandler("refund", refund))
app.add_handler(CommandHandler("adduser", adduser))
app.add_handler(CommandHandler("removeuser", removeuser))

# handler simpan list
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, simpan_list))

# set menu Telegram
app.post_init = set_commands

print("BOT SUDAH AKTIF YA GANTENG✅")
app.run_polling()
