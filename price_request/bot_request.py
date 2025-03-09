import os
import asyncio
import aiohttp
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.error import TelegramError
from datetime import datetime
from bs4 import BeautifulSoup
import nest_asyncio
import threading

# Allow nested event loops (required in some environments)
nest_asyncio.apply()

# Retrieve environment variables
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # e.g., "https://your-app.onrender.com/webhook"
if not BOT_TOKEN:
    raise ValueError("Missing TELEGRAM_BOT_TOKEN environment variable!")
if not WEBHOOK_URL:
    raise ValueError("Missing WEBHOOK_URL environment variable!")

# Use NOW from your util if available; otherwise, fallback to current datetime.
try:
    from util.utils import NOW
except ImportError:
    NOW = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Initialize Flask app
app = Flask(__name__)

@app.route("/")
def health_check():
    return "Bot is running!", 200

# Webhook endpoint for Telegram updates
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(force=True)
    if data:
        update = Update.de_json(data, app.bot)
        # Process the update asynchronously
        asyncio.create_task(app.application.process_update(update))
    return "ok", 200

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

async def main():
    """Set up and run the Telegram bot in webhook mode."""
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("price", price))

    # Save bot and application in the Flask app for use in the webhook endpoint
    app.application = application
    app.bot = application.bot

    # Remove any existing webhook, then set the new one
    try:
        await app.bot.delete_webhook(drop_pending_updates=True)
        await app.bot.set_webhook(WEBHOOK_URL)
        print(f"Webhook set to: {WEBHOOK_URL}")
    except TelegramError as te:
        print(f"Error setting webhook: {te}")

    print("Telegram bot is running in webhook mode.")

    # Keep the async loop alive indefinitely.
    while True:
        await asyncio.sleep(3600)

def run_flask():
    """Run Flask server; Render supplies the PORT environment variable."""
    flask_port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=flask_port, use_reloader=False)

if __name__ == "__main__":
    # Start Flask in a separate thread so it can serve health-check and webhook endpoints.
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    # Run the asynchronous main() in the main thread.
    asyncio.run(main())
