import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
from dateutil import tz


def parse_gold_price():
    url = "https://webgia.com/gia-vang/doji/"
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Error fetching data: {response.status_code}")
    html = response.text
    soup = BeautifulSoup(html, "html.parser")
    
    # Find the table cell containing the identifier text.
    row_td = soup.find("td", string="Nhẫn tròn 999 Hưng Thịnh Vượng")
    if not row_td:
        raise Exception("Gold price information not found.")
    
    # Get the parent row and then all the cells.
    row = row_td.find_parent("tr")
    tds = row.find_all("td")
    if len(tds) < 2:
        raise Exception("Incomplete price data.")
    
    # Assuming the buying price is in the second-to-last cell and selling price in the last cell.
    mua_vao = tds[-2].get_text(strip=True)
    ban_ra = tds[-1].get_text(strip=True)
    
    data = {
        "updated": datetime.utcnow().replace(tzinfo=tz.UTC).astimezone(tz.tzlocal())
                    .strftime("%Y-%m-%d %H:%M:%S UTC+7"),
        "mua_vao": mua_vao,
        "ban_ra": ban_ra
    }
    return data

if __name__ == "__main__":
    try:
        data = parse_gold_price()
        # Print the JSON data (this output will be captured by GitHub Actions)
        print(json.dumps(data, indent=2, ensure_ascii=False))
    except Exception as e:
        print("Error:", e)
