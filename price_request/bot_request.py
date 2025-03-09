import os
import aiohttp
from bs4 import BeautifulSoup
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from datetime import datetime
import threading
import asyncio
import logging

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

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        logger.error(f"Error in price command: {e}")
        await update.message.reply_text(f"Error: {str(e)}")

async def start_bot():
    """Start the Telegram bot"""
    try:
        application = Application.builder().token(BOT_TOKEN).build()
        application.add_handler(CommandHandler("price", price))
        logger.info("Telegram bot is running...")
        await application.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        logger.error(f"Telegram bot failed: {e}")
        # Shutdown the application if the bot fails
        os._exit(1)

def run_flask():
    """Run Flask in a separate thread."""
    flask_port = int(os.getenv("PORT", 5000))
    logger.info(f"Starting Flask server on port {flask_port}...")
    app.run(
        host='0.0.0.0',
        port=flask_port,
        use_reloader=False,
        threaded=True
    )

def run_app():
    """Run Flask and Telegram bot concurrently."""
    # Start Flask in a separate thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # Create a new event loop for the Telegram bot
    bot_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(bot_loop)
    bot_loop.run_until_complete(start_bot())

if __name__ == "__main__":
    run_app()