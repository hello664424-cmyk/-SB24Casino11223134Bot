import os
import random
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# Mock database: balance dictionary per user_id
user_balances = {}
INITIAL_BALANCE = 1000

def get_balance(user_id: int) -> int:
    return user_balances.setdefault(user_id, INITIAL_BALANCE)

def update_balance(user_id: int, amount: int):
    user_balances[user_id] = get_balance(user_id) + amount

# --- Keyboards ---
def main_menu_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("🎰 Slots", callback_data="game_slots"),
            InlineKeyboardButton("🎲 Dice", callback_data="game_dice"),
        ],
        [
            InlineKeyboardButton("🪙 Coin Flip", callback_data="game_coin"),
            InlineKeyboardButton("💰 Balance", callback_data="check_balance"),
        ],
        [
            InlineKeyboardButton("🎁 Daily Bonus", callback_data="daily_bonus"),
            InlineKeyboardButton("🚀 Share / Boost", callback_data="share_bot"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)

def back_keyboard():
    keyboard = [[InlineKeyboardButton("🔙 Back to Casino", callback_data="main_menu")]]
    return InlineKeyboardMarkup(keyboard)

# --- Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    get_balance(user.id)
    text = (
        f"🎰 *Welcome to the Telegram Casino, {user.first_name}!*\n\n"
        f"You start with a balance of *${INITIAL_BALANCE}* credits.\n"
        "Choose an option below to start playing and boost your balance!"
    )
    if update.message:
        await update.message.reply_text(text, parse_mode="Markdown", reply_markup=main_menu_keyboard())
    elif update.callback_query:
        await update.callback_query.message.edit_text(text, parse_mode="Markdown", reply_markup=main_menu_keyboard())

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    if data == "main_menu":
        await start(update, context)

    elif data == "check_balance":
        balance = get_balance(user_id)
        text = f"💰 *Your Current Balance:* `${balance}` credits"
        await query.message.edit_text(text, parse_mode="Markdown", reply_markup=back_keyboard())

    elif data == "daily_bonus":
        bonus = 200
        update_balance(user_id, bonus)
        text = f"🎁 *Daily Bonus Claimed!*\n\nYou received +${bonus} credits!\nNew Balance: `${get_balance(user_id)}`"
        await query.message.edit_text(text, parse_mode="Markdown", reply_markup=back_keyboard())

    elif data == "game_slots":
        bet = 50
        if get_balance(user_id) < bet:
            await query.message.edit_text("❌ *Insufficient balance!*", parse_mode="Markdown", reply_markup=back_keyboard())
            return

        symbols = ["🍒", "🍋", "7️⃣", "💎", "🔔"]
        reel = [random.choice(symbols) for _ in range(3)]
        
        if reel[0] == reel[1] == reel[2]:
            win = bet * 10
            update_balance(user_id, win - bet)
            result = f"🎉 *JACKPOT!* You won `${win}` credits!"
        elif reel[0] == reel[1] or reel[1] == reel[2] or reel[0] == reel[2]:
            win = bet * 2
            update_balance(user_id, win - bet)
            result = f"✨ *Match 2!* You won `${win}` credits!"
        else:
            update_balance(user_id, -bet)
            result = f"💸 You lost `${bet}` credits. Try again!"

        text = (
            f"🎰 *SLOT MACHINE*\n\n"
            f"[ {reel[0]} | {reel[1]} | {reel[2]} ]\n\n"
            f"{result}\n"
            f"Current Balance: `${get_balance(user_id)}`"
        )
        await query.message.edit_text(text, parse_mode="Markdown", reply_markup=back_keyboard())

    elif data == "game_dice":
        bet = 50
        if get_balance(user_id) < bet:
            await query.message.edit_text("❌ *Insufficient balance!*", parse_mode="Markdown", reply_markup=back_keyboard())
            return

        user_roll = random.randint(1, 6)
        bot_roll = random.randint(1, 6)

        if user_roll > bot_roll:
            win = bet * 2
            update_balance(user_id, bet)
            result = f"🎉 *You Won!* `${win}` credits!"
        elif user_roll < bot_roll:
            update_balance(user_id, -bet)
            result = f"💸 *Bot Won!* You lost `${bet}` credits."
        else:
            result = "🤝 *It's a Tie!* Bet refunded."

        text = (
            f"🎲 *DICE ROLL*\n\n"
            f" You rolled: *{user_roll}*\n"
            f"🤖 Bot rolled: *{bot_roll}*\n\n"
            f"{result}\n"
            f"Current Balance: `${get_balance(user_id)}`"
        )
        await query.message.edit_text(text, parse_mode="Markdown", reply_markup=back_keyboard())

    elif data == "game_coin":
        bet = 50
        if get_balance(user_id) < bet:
            await query.message.edit_text("❌ *Insufficient balance!*", parse_mode="Markdown", reply_markup=back_keyboard())
            return

        outcome = random.choice(["Heads", "Tails"])
        user_choice = random.choice(["Heads", "Tails"])

        if outcome == user_choice:
            update_balance(user_id, bet)
            result = f"🎉 Coin landed on *{outcome}*! You won `${bet * 2}`!"
        else:
            update_balance(user_id, -bet)
            result = f"💸 Coin landed on *{outcome}*! You lost `${bet}`."

        text = (
            f"🪙 *COIN FLIP*\n\n"
            f"Your Pick: *{user_choice}*\n"
            f"Result: *{outcome}*\n\n"
            f"{result}\n"
            f"Current Balance: `${get_balance(user_id)}`"
        )
        await query.message.edit_text(text, parse_mode="Markdown", reply_markup=back_keyboard())

    elif data == "share_bot":
        text = (
            "🚀 *Boost & Share*\n\n"
            "Share this bot with your friends or add it to your channel/group to gain extra perks!"
        )
        await query.message.edit_text(text, parse_mode="Markdown", reply_markup=back_keyboard())

def main():
    token = os.environ.get("BOT_TOKEN")
    if not token:
        raise ValueError("BOT_TOKEN environment variable is not set!")

    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    logging.info("Bot started...")
    app.run_polling()

if __name__ == "__main__":
    main()
