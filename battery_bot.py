import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# ─────────────────────────────────────────────
# CONFIGURATION — modifie ces valeurs
 import os
TOKEN = os.environ.get('8719214633:AAHi3TQj_CknX5cbhcWBfIBZiMUFvhAhU8c')         # Token donné par @BotFather
ALLOWED_USERS = []               # Laisse vide pour tout le monde, ou mets [123456789, 987654321]
# ─────────────────────────────────────────────

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Stockage en mémoire : { user_id: {"name": str, "battery": int} }
battery_store: dict = {}

BATTERY_LEVELS = [5, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]

def battery_emoji(level: int) -> str:
    if level >= 80:
        return "🟢"
    elif level >= 40:
        return "🟡"
    elif level >= 15:
        return "🟠"
    else:
        return "🔴"

def format_status(user_data: dict, name: str) -> str:
    lvl = user_data.get("battery")
    if lvl is None:
        return f"*{name}* — pas encore renseigné"
    bar_filled = round(lvl / 10)
    bar = "█" * bar_filled + "░" * (10 - bar_filled)
    return f"{battery_emoji(lvl)} *{name}* — `{bar}` {lvl}%"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in battery_store:
        battery_store[user.id] = {"name": user.first_name, "battery": None}
    await update.message.reply_text(
        "🔋 *Bot Batterie* — Bonjour !\n\n"
        "Commandes disponibles :\n"
        "• /batterie — Envoyer ta batterie\n"
        "• /statut — Voir les batteries de tout le monde\n"
        "• /aide — Aide",
        parse_mode="Markdown",
    )

async def batterie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Affiche un clavier inline pour choisir son niveau de batterie."""
    keyboard = []
    row = []
    for i, lvl in enumerate(BATTERY_LEVELS):
        emoji = battery_emoji(lvl)
        row.append(InlineKeyboardButton(f"{emoji} {lvl}%", callback_data=f"bat_{lvl}"))
        if len(row) == 3 or i == len(BATTERY_LEVELS) - 1:
            keyboard.append(row)
            row = []
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Choisis ton niveau de batterie :", reply_markup=reply_markup
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user

    if query.data.startswith("bat_"):
        level = int(query.data.split("_")[1])
        if user.id not in battery_store:
            battery_store[user.id] = {"name": user.first_name, "battery": None}
        battery_store[user.id]["battery"] = level
        battery_store[user.id]["name"] = user.first_name

        await query.edit_message_text(
            f"✅ Batterie mise à jour : {battery_emoji(level)} *{level}%*",
            parse_mode="Markdown",
        )

        # Notifie les autres utilisateurs enregistrés
        msg = f"📡 *{user.first_name}* vient de mettre sa batterie à {battery_emoji(level)} *{level}%*"
        for uid, data in battery_store.items():
            if uid != user.id:
                try:
                    await context.bot.send_message(uid, msg, parse_mode="Markdown")
                except Exception:
                    pass

async def statut(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Affiche l'état de la batterie de tout le monde."""
    user = update.effective_user
    if user.id not in battery_store:
        battery_store[user.id] = {"name": user.first_name, "battery": None}

    if not battery_store:
        await update.message.reply_text("Aucune batterie enregistrée pour l'instant.")
        return

    lines = ["🔋 *Statut des batteries :*\n"]
    for uid, data in battery_store.items():
        lines.append(format_status(data, data["name"]))

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

async def aide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 *Aide — Bot Batterie*\n\n"
        "/batterie — Envoie ton niveau de batterie\n"
        "/statut — Voir tous les niveaux\n"
        "/aide — Ce message\n\n"
        "_Quand tu mets à jour ta batterie, ton/ta partenaire reçoit une notification automatique !_",
        parse_mode="Markdown",
    )

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("batterie", batterie))
    app.add_handler(CommandHandler("statut", statut))
    app.add_handler(CommandHandler("aide", aide))
    app.add_handler(CallbackQueryHandler(button_callback))
    logger.info("Bot démarré ✅")
    app.run_polling()

if __name__ == "__main__":
    main()
