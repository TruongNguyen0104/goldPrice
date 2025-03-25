import os
import asyncio
import aiohttp
import json
import time
from bs4 import BeautifulSoup
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.error import Conflict
from flask import Flask
import threading

# Retrieve the bot token from the environment variable.
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("Missing TELEGRAM_BOT_TOKEN environment variable!")

# Cache settings: store the scraped data to reduce repeated HTTP requests.
CACHE_FILE = "price_cache.json"
CACHE_TTL = 300  # seconds (5 minutes)

def escape_md(text):
    """Escape special characters for MarkdownV2."""
    escape_chars = "_*[]()~`>#+-=|{}.!\\"
    return "".join(f"\\{char}" if char in escape_chars else char for char in text)

async def fetch_price():
    """Scrape the gold price from the target URL."""
    URL = "https://webgia.com/gia-vang/doji/"
    async with aiohttp.ClientSession() as session:
        async with session.get(URL) as response:
            if response.status != 200:
                raise Exception("Website error")
            page_content = await response.text()
    soup = BeautifulSoup(page_content, "html.parser")
    row_td = soup.find("td", string="Nhẫn tròn 999 Hưng Thịnh Vượng")
    if not row_td:
        raise Exception("Gold price information not found.")
    row = row_td.find_parent("tr")
    tds = row.find_all("td")
    if len(tds) < 2:
        raise Exception("Gold price data incomplete.")
    hcm_price = {
        "Mua vào": escape_md(tds[-2].get_text(strip=True)),
        "Bán ra": escape_md(tds[-1].get_text(strip=True)),
    }
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = (
        f"\U0001F4E2 *DOJI Gold Price Update* \U0001F3C6\n"
        f"\U0001F4C5 *Date:* {escape_md(now_str)}\n\n"
        f"\U0001F4B0 *Mua vào:* {hcm_price['Mua vào']}\n"
        f"\U0001F4B0 *Bán ra:* {hcm_price['Bán ra']}\n"
    )
    return message

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command handler to fetch and send the gold price."""
    try:
        # Try to load data from cache if it's still fresh.
        if os.path.exists(CACHE_FILE):
            mod_time = os.path.getmtime(CACHE_FILE)
            if time.time() - mod_time < CACHE_TTL:
                with open(CACHE_FILE, "r") as f:
                    cached = json.load(f)
                await update.message.reply_text(cached["message"], parse_mode="MarkdownV2")
                return

        # Otherwise, scrape the website.
        message = await fetch_price()
        # Save the result to cache.
        with open(CACHE_FILE, "w") as f:
            json.dump({"message": message, "timestamp": time.time()}, f)
        await update.message.reply_text(message, parse_mode="MarkdownV2")
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

async def run_polling():
    """Run the Telegram bot polling for a short period then exit."""
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("price", price))
    
    # Attempt to delete any existing webhook to avoid conflicts.
    try:
        await application.bot.delete_webhook(drop_pending_updates=True)
    except Exception as e:
        print("Error deleting webhook:", e)
    
    await application.initialize()
    await application.start_polling()
    print("Polling started. Running for a limited time...")
    # Poll for a fixed duration (e.g., 20 seconds) to save CPU.
    await asyncio.sleep(20)
    await application.stop()
    await application.shutdown()
    print("Polling stopped.")

def run_flask():
    """Run a minimal Flask server for uptime monitoring."""
    app = Flask(__name__)
    
    @app.route("/")
    def health_check():
        return "Bot is running!", 200

    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, use_reloader=False)

def main():
    # Start the Flask server in a background thread.
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Run the Telegram bot polling.
    asyncio.run(run_polling())

if __name__ == "__main__":
    main()
