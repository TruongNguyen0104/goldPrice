import os
import aiohttp
from bs4 import BeautifulSoup
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from datetime import datetime
import threading
import asyncio

# Ensure BOT_TOKEN is provided
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("Missing TELEGRAM_BOT_TOKEN environment variable!")

# Use NOW from your util if available; otherwise, fallback to datetime.
try:
    from util.utils import NOW
except ImportError:
    NOW = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Initialize Flask app
app = Flask(__name__)

@app.route("/")
def health_check():
    return "Bot is running!", 200

def escape_md(text):
    """Escape special characters for MarkdownV2"""
    escape_chars = "_*[]()~`>#+-=|{}.!"
    return "".join(f"\\{char}" if char in escape_chars else char for char in text)

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fetch and send gold price"""
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

async def start_bot():
    """Start the Telegram bot"""
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("price", price))
    print("Telegram bot is running...")
    # Disable signal handling since this is running in a non-main thread.
    await application.run_polling(allowed_updates=Update.ALL_TYPES, handle_signals=False)

def run_telegram_bot():
    """Run Telegram bot in its own event loop."""
    new_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(new_loop)
    new_loop.run_until_complete(start_bot())

def run_app():
    """Run Flask and Telegram bot concurrently."""
    # Start Flask in a separate thread
    flask_port = int(os.getenv("PORT", 5000))
    flask_thread = threading.Thread(
        target=app.run,
        kwargs={
            'host': '0.0.0.0',
            'port': flask_port,
            'use_reloader': False,
            'threaded': True
        },
        daemon=True
    )
    flask_thread.start()

    # Start the Telegram bot in its own thread with a separate event loop
    bot_thread = threading.Thread(target=run_telegram_bot, daemon=True)
    bot_thread.start()

    # Keep the main thread alive
    flask_thread.join()
    bot_thread.join()

if __name__ == "__main__":
    run_app()
