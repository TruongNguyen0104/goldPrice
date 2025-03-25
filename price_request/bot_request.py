import os
import aiohttp
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# URL of the JSON file from GitHub
JSON_URL = "https://raw.githubusercontent.com/TruongNguyen0104/goldPrice/main/data/doji_price.json"

def format_currency(value: str) -> str:
    """Convert a number string like '9.610.000' into a formatted currency string."""
    try:
        clean_value = value.replace('.', '')  # Remove dots
        return f"{int(clean_value):,} VND"  # Convert to integer and format with commas
    except ValueError:
        return "N/A"

def escape_markdown(text: str) -> str:
    """
    Escapes Telegram MarkdownV2 reserved characters in the provided text.
    Reserved characters include: '_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!'
    """
    reserved_chars = ["_", "*", "[", "]", "(", ")", "~", "`", ">", "#", "+", "-", "=", "|", "{", "}", ".", "!"]
    for char in reserved_chars:
        text = text.replace(char, f"\\{char}")
    return text

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    headers = {"Accept": "application/json"}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(JSON_URL, headers=headers, timeout=10) as response:
                if response.status != 200:
                    await update.message.reply_text("⚠️ Cannot fetch gold price data.")
                    return

                try:
                    # Force JSON parsing regardless of Content-Type
                    data = await response.json(content_type=None)
                except aiohttp.ContentTypeError:
                    raw_text = await response.text()
                    await update.message.reply_text(f"⚠️ Error: Invalid data format.\n{raw_text}")
                    return

        # Extract and escape data
        updated_raw = data.get("updated", "N/A")
        buy_raw = data.get("mua_vao", "0")
        sell_raw = data.get("ban_ra", "0")

        updated = escape_markdown(updated_raw)
        buy_price = escape_markdown(format_currency(buy_raw))
        sell_price = escape_markdown(format_currency(sell_raw))

        # Construct the response message with MarkdownV2 formatting
        message = (
            f"📢 *DOJI Gold Price Update*\n"
            f"📅 *Updated:* {updated}\n\n"
            f"💰 *Buy:* {buy_price}\n"
            f"💰 *Sell:* {sell_price}"
        )

        await update.message.reply_text(message, parse_mode="MarkdownV2")
    except asyncio.TimeoutError:
        await update.message.reply_text("⏳ Connection timed out. Please try again later.")
    except aiohttp.ClientError as e:
        await update.message.reply_text(f"⚠️ Connection error: {str(e)}")
    except Exception as e:
        await update.message.reply_text(f"❌ Unknown error: {str(e)}")

def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    token = "7466414955:AAHWl7kQR-HSj2YgnxdUCUN2mJ9nwej-mUk"
    if not token:
        raise ValueError("❌ Missing environment variable TELEGRAM_BOT_TOKEN!")

    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler("price", price))
    application.run_polling()

if __name__ == "__main__":
    main()
