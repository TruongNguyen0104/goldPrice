import requests
import os
import re
import time
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone

class TelegramBot:
    """Handles sending messages to Telegram."""

    def __init__(self, bot_token, chat_id):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"

    def escape_markdown(self, text):
        """Escapes special characters for Telegram MarkdownV2."""
        if not isinstance(text, str):
            text = str(text)
        return re.sub(r'([_*\[\]()~`>#+\-=|{}.!])', r'\\\1', text)

    def format_message(self, rows):
        """Formats the message with gold price updates."""
        if not rows:
            return None

        message = "📢 *Gold Price Update* 🏆\n"

        for index, row in enumerate(rows):
            if index == 0:  # First row includes Date & Brand
                message += (
                    f"\n🗓 *Date:* {self.escape_markdown(row['Date'])}\n"
                    f"🏢 *Brand:* {self.escape_markdown(row['Brand'])}\n\n"
                )

            message += (
                f"💎 *Type:* {self.escape_markdown(row['Type'])}\n"
                f"💰 *Buy Price:* {self.escape_markdown(row['Buy'])}\n"
                f"   📈 Change: {self.escape_markdown(row['Buy Change'])}\n"
                f"💵 *Sell Price:* {self.escape_markdown(row['Sell'])}\n"
                f"   📉 Change: {self.escape_markdown(row['Sell Change'])}\n\n"
            )

        return message

    def send_message(self, rows):
        """Sends a formatted message to Telegram."""
        if not self.bot_token or not self.chat_id:
            print("Telegram credentials are missing!")
            return

        message = self.format_message(rows)
        if not message:
            return

        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "MarkdownV2"
        }

        try:
            response = requests.post(self.api_url, json=payload)
            res_json = response.json()
            if res_json.get("ok"):
                print("Message sent successfully!")
            else:
                print(f"Failed to send message: {res_json}")
        except Exception as e:
            print(f"Error sending Telegram message: {e}")

        time.sleep(5)  # Avoid Telegram rate limits


class GoldPriceScraper:
    """Scrapes gold prices from the specified website."""

    BASE_URL = "https://giavang.org/trong-nuoc/"

    def __init__(self):
        self.df = pd.DataFrame(columns=['Date', 'Brand', 'Type', 'Buy', 'Buy Change', 'Sell', 'Sell Change'])

    def fetch_gold_price(self, brand):
        """Scrapes gold prices for the given brand."""
        url = f"{self.BASE_URL}{brand}/"
        response = requests.get(url)

        if response.status_code != 200:
            print(f"Failed to retrieve the webpage for {brand}.")
            return []

        soup = BeautifulSoup(response.content, 'html.parser')
        timestamp_element = soup.find('h1', class_='box-headline highlight')
        gold_price_element = soup.find('div', class_='gold-price-box')

        if not timestamp_element or not gold_price_element:
            print(f"Gold price data not found for {brand}.")
            return []

        timestamp = self.extract_timestamp(timestamp_element.text)
        gold_prices = self.extract_gold_prices(gold_price_element)

        return self.process_gold_prices(brand, timestamp, gold_prices)

    @staticmethod
    def extract_timestamp(text):
        """Extracts the timestamp from the HTML element."""
        parts = text.split(' ')
        return f"{parts[-1]} {parts[-2]}"

    @staticmethod
    def extract_gold_prices(element):
        """Extracts and cleans gold price data from the HTML element."""
        gold_prices = element.getText().strip().split('\n')
        return list(filter(None, gold_prices))  # Remove empty strings

    def process_gold_prices(self, brand, timestamp, gold_prices):
        """Processes extracted gold prices and structures them into dictionary format."""
        new_rows = []

        if len(gold_prices) < 7:
            return []

        new_rows.append({
            'Date': timestamp,
            'Brand': brand.upper(),
            'Type': "Bullion" if "Miếng" in gold_prices[0] else "Ring",
            'Buy': gold_prices[2],
            'Buy Change': gold_prices[3],
            'Sell': gold_prices[5],
            'Sell Change': gold_prices[6]
        })

        if len(gold_prices) > 7:
            new_rows.append({
                'Date': timestamp,
                'Brand': brand.upper(),
                'Type': "Bullion" if "Miếng" in gold_prices[7] else "Ring",
                'Buy': gold_prices[9],
                'Buy Change': gold_prices[10],
                'Sell': gold_prices[12],
                'Sell Change': gold_prices[13]
            })

        return new_rows

    def scrape_all_brands(self, brands):
        """Scrapes gold prices for multiple brands."""
        all_new_rows = []

        for brand in brands:
            new_rows = self.fetch_gold_price(brand)
            if new_rows:
                self.df = pd.concat([self.df, pd.DataFrame(new_rows)], ignore_index=True)
                all_new_rows.extend(new_rows)

        return all_new_rows


class CSVHandler:
    """Handles saving data to CSV files."""

    def __init__(self, directory="data"):
        self.output_dir = os.path.join(os.getcwd(), directory)
        os.makedirs(self.output_dir, exist_ok=True)

        gmt_plus_7 = timezone(timedelta(hours=7))
        today = datetime.now(gmt_plus_7).strftime("%Y-%m-%d-%H%M%S")

        self.csv_filename = os.path.join(self.output_dir, "gold_price.csv")
        self.alternate_csv_filename = os.path.join(self.output_dir, f"gold_price_{today}.csv")

    def save_to_csv(self, df):
        """Saves the DataFrame to a CSV file."""
        try:
            df.to_csv(self.csv_filename, index=False, encoding='utf-8-sig', mode='a', header=not os.path.exists(self.csv_filename))
            print("Data saved to CSV file.")
        except:
            print("Failed to save data to the main CSV file. Saving to alternate file.")
            df.to_csv(self.alternate_csv_filename, index=False, encoding='utf-8-sig', mode='w')


def main():
    """Main function to run the script."""
    # Load Telegram credentials from environment variables
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

    brands = ['doji', 'pnj', 'sjc', 'phu-quy', 'bao-tin-minh-chau', 'bao-tin-manh-hai', 'mi-hong', 'ngoc-tham']

    scraper = GoldPriceScraper()
    telegram_bot = TelegramBot(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
    csv_handler = CSVHandler()

    all_new_rows = scraper.scrape_all_brands(brands)

    if any(brand == 'doji' for brand in brands):
        telegram_bot.send_message(all_new_rows)

    csv_handler.save_to_csv(scraper.df)


if __name__ == "__main__":
    main()
