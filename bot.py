import os
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Simulated User Balances (In-Memory Database)
USER_BALANCES = {}
STARTING_BALANCE = 1000

def get_balance(user_id: int) -> int:
    return USER_BALANCES.setdefault(user_id, STARTING_BALANCE)

def update_balance(user_id: int, amount: int) -> int:
    USER_BALANCES[user_id] = get_balance(user_id) + amount
    return USER_BALANCES[user_id]


def get_game_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("🎰 Slots (Bet 100)", callback_data="game_slot"),
            InlineKeyboardButton("🎲 Dice (Bet 100)", callback_data="game_dice"),
        ],
        [
            InlineKeyboardButton("🎳 Bowling (Bet 100)", callback_data="game_bowling"),
            InlineKeyboardButton("🎯 Darts (Bet 100)", callback_data="game_darts"),
        ],
        [
            InlineKeyboardButton("💰 Check Balance", callback_data="check_balance"),
            InlineKeyboardButton("🎁 Daily Bonus", callback_data="daily_bonus"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    balance = get_balance(user.id)
    
    welcome_text = (
        f"🎰 **Welcome to the Telegram Casino, {user.first_name}!** 🎰\n\n"
        f"💵 Your Current Balance: **${balance}**\n\n"
        f"Select a game below to place a bet (Default bet: $100):"
    )
    
    await update.message.reply_text(
        welcome_text, parse_mode="Markdown", reply_markup=get_game_keyboard()
    )


async def handle_game_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    balance = get_balance(user_id)
    bet_amount = 100

    if query.data == "check_balance":
        await query.message.reply_text(f"💵 Your Current Balance: **${balance}**", parse_mode="Markdown")
        return

    if query.data == "daily_bonus":
        update_balance(user_id, 500)
        new_bal = get_balance(user_id)
        await query.message.reply_text(f"🎁 You claimed $500 daily bonus!\nNew Balance: **${new_bal}**", parse_mode="Markdown")
        return

    if balance < bet_amount:
        await query.message.reply_text("❌ You don't have enough balance! Claim your bonus or check back later.")
        return

    # Deduct bet amount
    update_balance(user_id, -bet_amount)

    # Determine game emoji
    emoji_map = {
        "game_slot": "🎰",
        "game_dice": "🎲",
        "game_bowling": "🎳",
        "game_darts": "🎯",
    }
    emoji = emoji_map.get(query.data, "🎲")

    # Send native interactive Telegram animated dice/slot
    msg = await query.message.reply_dice(emoji=emoji)
    value = msg.dice.value

    # Wait for Telegram's animation to finish
    await asyncio.sleep(3.5)

    # Outcome logic
    payout = 0
    if query.data == "game_slot":
        # Slot machine values: 64 is Jackpot (777), 1, 22, 43 are 3-in-a-row combos
        if value == 64:
            payout = 1000  # Grand Jackpot
            res_text = "🎉 **JACKPOT 777!** You won $1000!"
        elif value in [1, 22, 43]:
            payout = 300   # Triple Combo
            res_text = f"✨ **3-in-a-row!** You won ${payout}!"
        elif value > 30:
            payout = 150   # Small win
            res_text = f"🎉 **Small Win!** You won ${payout}!"
        else:
            res_text = "❌ No luck this time!"

    elif query.data == "game_dice":
        if value >= 5:
            payout = 250
            res_text = f"🎉 You rolled a {value}! You won ${payout}!"
        elif value == 4:
            payout = 100
            res_text = f"🤝 You rolled a {value}! Bet returned (${payout})."
        else:
            res_text = f"❌ You rolled a {value}! Better luck next time."

    elif query.data == "game_bowling":
        if value == 6:
            payout = 400
            res_text = "💥 **STRIKE!** You won $400!"
        elif value >= 4:
            payout = 150
            res_text = f"🎳 Nice shot ({value} pins)! You won ${payout}."
        else:
            res_text = f"❌ Only {value} pins down. Loss!"

    elif query.data == "game_darts":
        if value == 6:
            payout = 500
            res_text = "🎯 **BULLSEYE!** You won $500!"
        elif value >= 4:
            payout = 150
            res_text = f"🎯 Good hit! You won ${payout}."
        else:
            res_text = "❌ Missed the center!"

    update_balance(user_id, payout)
    final_balance = get_balance(user_id)

    await query.message.reply_text(
        f"{res_text}\n💵 New Balance: **${final_balance}**",
        parse_mode="Markdown",
        reply_markup=get_game_keyboard(),
    )


def main():
    token = os.getenv("BOT_TOKEN")
    if not token:
        logger.error("BOT_TOKEN environment variable is missing!")
        return

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CallbackQueryHandler(handle_game_choice))

    logger.info("Bot starting...")
    app.run_polling()


if __name__ == "__main__":
    main()
