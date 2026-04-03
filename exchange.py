import requests
import csv
from datetime import datetime, timezone, timedelta
import os

FILE = "exchange_rates.csv"

def get_rate(base, target):
    url = f"https://api.frankfurter.app/latest?from={base}&to={target}"
    response = requests.get(url, timeout=20)
    response.raise_for_status()
    data = response.json()
    return data["rates"][target]

def save_rates():
    beijing_tz = timezone(timedelta(hours=8))
    timestamp = datetime.now(beijing_tz).strftime("%Y-%m-%d %H:%M")

    usd_cny = get_rate("USD", "CNY")
    gbp_usd = get_rate("GBP", "USD")
    eur_usd = get_rate("EUR", "USD")

    file_exists = os.path.isfile(FILE)

    with open(FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        if not file_exists:
            writer.writerow(["timestamp", "USD_CNY", "GBP_USD", "EUR_USD"])

        writer.writerow([timestamp, usd_cny, gbp_usd, eur_usd])

    print("Saved one row to exchange_rates.csv")

if __name__ == "__main__":
    save_rates()
