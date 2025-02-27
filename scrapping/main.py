import requests
import os
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta, timezone

# Get current time in GMT+7
gmt_plus_7 = timezone(timedelta(hours=7))
TODAY = datetime.now(gmt_plus_7).strftime("%Y-%m-%d-%H%M%S")  # Get the current date and time

output_dir = os.path.join(os.getcwd(), "data")
csv_filename = os.path.join(output_dir, "gold_price.csv")
alternate_csv_filename = os.path.join(output_dir, f"gold_price_{TODAY}.csv")


df = pd.DataFrame(columns=['Date','Brand','Type','Buy','Buy Change','Sell','Sell Change'])   # Create a new DataFrame to store the data

# URL of the webpage to scrape
for brand in ['doji','pnj','sjc','phu-quy','bao-tin-minh-chau','bao-tin-manh-hai','mi-hong','ngoc-tham']:
    url = f"https://giavang.org/trong-nuoc/{brand}/"

    # Send a GET request to the webpage
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the HTML content of the webpage
        soup = BeautifulSoup(response.content, 'html.parser')

       # Find the element on the webpage
        timestamp = soup.find('h1', class_='box-headline highlight')  # Get the timestamp
        gold_price = soup.find('div', class_='gold-price-box')  #Get the gold price
        
        timestamp = timestamp.text.split(' ')[-1] + ' ' + timestamp.text.split(' ')[-2]
        # Check if the element exists
        if gold_price:
            gold_price = gold_price.getText().strip().split('\n')
            gold_price = list(filter(None ,gold_price)) # Remove empty strings from the list

            """ the data to the DataFrame
                bullion vs ring
            """
            
            df = df.append({'Date': timestamp, 
                    'Brand': brand.upper(),
                    'Type': "Bullion" if "Miếng" in gold_price[0] else "Ring",
                    'Buy':gold_price[2],
                    'Buy Change':gold_price[3],
                    'Sell':gold_price[5],
                    'Sell Change':gold_price[6]}, ignore_index=True)
            
            if len(gold_price) > 7:
                df = df.append({'Date': timestamp, 
                        'Brand': brand.upper(),
                        'Type': "Bullion" if "Miếng" in gold_price[7] else "Ring",
                        'Buy':gold_price[9],
                        'Buy Change':gold_price[10],
                        'Sell':gold_price[12],
                        'Sell Change':gold_price[13]}, ignore_index=True)
            
        else:
            print('Gold price not found.')
    else:
        print('Failed to retrieve the webpage.')
try:
    df.to_csv(csv_filename, index=False,encoding='utf-8-sig',mode='a')  # Save the data to a CSV file
    print('Data saved to CSV file.')
except:
    print('Failed to save the data to the main CSV file. System will try to save the data to a new CSV file.')
    df.to_csv(alternate_csv_filename, index=False,encoding='utf-8-sig', mode='w')  # Save the data to a CSV file
 
