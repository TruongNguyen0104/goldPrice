import os
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.error import Conflict
import nest_asyncio

# Allow nested event loops in environments that already have one running.
nest_asyncio.apply()

# Retrieve the bot token from environment variables.
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("Missing TELEGRAM_BOT_TOKEN environment variable!")

# Optionally, import a custom NOW; otherwise, use the current datetime.
try:
    from util.utils import NOW
except ImportError:
    NOW = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def escape_md(text):
    """Escape special characters for MarkdownV2."""
    escape_chars = "_*[]()~`>#+-=|{}.!"
    return "".join(f"\\{char}" if char in escape_chars else char for char in text)

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fetch and send gold price."""
    try:
        URL = "https://webgia.com/gia-vang/doji/"
        async with aiohttp.ClientSession() as session:
            async with session.get(URL) as response:
                if response.status != 200:
                    await update.message.reply_text("Price not found. Website error.")
                    return
                page_content = await response.text()
        soup = BeautifulSoup(page_content, "html.parser")
        row_td = soup.find("td", string="Nhẫn tròn 999 Hưng Thịnh Vượng")
        if not row_td:
            await update.message.reply_text("Gold price information not found.")
            return
        row = row_td.find_parent("tr")
        tds = row.find_all("td")
        if len(tds) < 2:
            await update.message.reply_text("Gold price data incomplete.")
            return
        hcm_price = {
            "Mua vào": escape_md(tds[-2].get_text(strip=True)),
            "Bán ra": escape_md(tds[-1].get_text(strip=True)),
        }
        message = (
            f"\U0001F4E2 *DOJI Gold Price Update* \U0001F3C6\n"
            f"\U0001F4C5 *Date:* {escape_md(NOW)}\n\n"
            f"\U0001F4B0 *Mua vào:* {hcm_price['Mua vào']}\n"
            f"\U0001F4B0 *Bán ra:* {hcm_price['Bán ra']}\n"
        )
        await update.message.reply_text(message, parse_mode="MarkdownV2")
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

async def run_polling():
    """Run the Telegram bot using long polling with retry logic."""
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("price", price))
    # Delete any existing webhook to avoid conflicts.
    try:
        await application.bot.delete_webhook(drop_pending_updates=True)
    except Exception as e:
        print("Error deleting webhook:", e)
    while True:
        try:
            print("Starting long polling...")
            await application.run_polling(allowed_updates=Update.ALL_TYPES)
        except Conflict as conflict_error:
            print(f"Conflict error: {conflict_error}. Retrying in 10 seconds...")
        except Exception as e:
            print(f"Unexpected error: {e}. Retrying in 10 seconds...")
        await asyncio.sleep(10)

def main():
    asyncio.run(run_polling())

if __name__ == "__main__":
    main()
