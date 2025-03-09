import asyncio
import threading
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

def start_flask_app():
    """Start the Flask app on the Render-assigned PORT."""
    port = int(os.getenv("PORT", 5000))  # Use Render PORT, default to 5000
    app.run(host="0.0.0.0", port=port, threaded=True)  # Allow multiple connections

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

def escape_md(text):
    """Escape special characters for MarkdownV2."""
    escape_chars = "_*[]()~`>#+-=|{}.!"
    return "".join(f"\\{char}" if char in escape_chars else char for char in text)

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fetch and send the latest gold price from the website."""
    try:
        URL = "https://webgia.com/gia-vang/doji/"
        async with aiohttp.ClientSession() as session:
            async with session.get(URL) as response:
                if response.status != 200:
                    await update.message.reply_text("Price not found. Website returned an error.")
                    return
                page_content = await response.text()

        soup = BeautifulSoup(page_content, "html.parser")
        row = soup.find("td", string="Nhẫn tròn 999 Hưng Thịnh Vượng")

        if not row:
            await update.message.reply_text("Could not find the gold price information.")
            return

        row = row.find_parent("tr")
        tds = row.find_all("td")

        if len(tds) < 7:
            await update.message.reply_text("Error parsing price data.")
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
    """Start the Telegram bot without closing the event loop."""
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("price", price))

    print("Bot is running...")
    
    # Run polling without closing the event loop
    await application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    try:
        # Start Flask in a separate thread
        flask_thread = threading.Thread(target=start_flask_app, daemon=True)
        flask_thread.start()

        # Use existing event loop instead of asyncio.run()
        loop = asyncio.get_running_loop()

        # Schedule `main()` as a non-blocking task
        loop.create_task(main())

        # Keep the event loop running
        loop.run_forever()

    except KeyboardInterrupt:
        print("Bot stopped by user.")
    except RuntimeError:
        # If `get_running_loop()` fails, fallback to creating a new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(main())
