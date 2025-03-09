import os
import aiohttp
from bs4 import BeautifulSoup
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from util.utils import NOW

# Initialize Flask app
app = Flask(__name__)

@app.route("/")
def health_check():
    return "Bot is running!", 200

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

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
        row = soup.find("td", string="Nhẫn tròn 999 Hưng Thịnh Vượng") or None

        if not row:
            await update.message.reply_text("Gold price information not found.")
            return

        row = row.find_parent("tr")
        tds = row.find_all("td")

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
    
    print("Bot is running...")
    await application.run_polling(allowed_updates=Update.ALL_TYPES)

def run_app():
    """Run both Flask and Telegram bot without additional libraries"""
    import threading
    import asyncio

    # Start Flask in a separate thread
    flask_thread = threading.Thread(
        target=app.run,
        kwargs={
            'host': '0.0.0.0',
            'port': int(os.getenv("PORT", 5000)),
            'use_reloader': False,
            'threaded': True
        },
        daemon=True
    )
    flask_thread.start()

    # Start Telegram bot in main thread
    asyncio.run(start_bot())

if __name__ == "__main__":
    run_app()