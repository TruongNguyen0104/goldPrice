import os
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from datetime import datetime
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import nest_asyncio
import threading

# Allow nested event loops (required in some environments)
nest_asyncio.apply()

# Retrieve the bot token from environment variables.
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("Missing TELEGRAM_BOT_TOKEN environment variable!")

# Use NOW from your util if available; otherwise, use the current time.
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

# Create a Flask app for health-checks.
app = Flask(__name__)

@app.route("/")
def health_check():
    return "Bot is running!", 200

def run_flask():
    """Run the Flask server using the PORT environment variable."""
    flask_port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=flask_port, use_reloader=False)

async def run_polling():
    """Set up the Telegram bot and run long polling."""
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("price", price))
    
    # Delete any pre-existing webhook to avoid conflicts.
    try:
        await application.bot.delete_webhook(drop_pending_updates=True)
    except Exception as e:
        print("Error deleting webhook:", e)
    
    print("Starting long polling...")
    await application.run_polling(allowed_updates=Update.ALL_TYPES)

def main():
    # Start the Flask health-check server in a separate daemon thread.
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # Use the current event loop for polling.
    loop = asyncio.get_event_loop()
    loop.create_task(run_polling())
    loop.run_forever()

if __name__ == "__main__":
    main()
