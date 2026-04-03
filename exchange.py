import requests
import csv
from datetime import datetime
import os

FILE = "exchange_rates.csv"

def get_rate(from_currency, to_currency):
    url = f"https://api.frankfurter.app/latest?from={from_currency}&to={to_currency}"
    res = requests.get(url)
    data = res.json()
    return data["rates"][to_currency]

def save_rates():
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    usd_cny = get_rate("USD", "CNY")
    gbp_usd = get_rate("GBP", "USD")
    eur_usd = get_rate("EUR", "USD")

    file_exists = os.path.isfile(FILE)

    with open(FILE, "a", newline="") as f:
        writer = csv.writer(f)

        if not file_exists:
            writer.writerow(["timestamp", "USD_CNY", "GBP_USD", "EUR_USD"])

        writer.writerow([now, usd_cny, gbp_usd, eur_usd])

if __name__ == "__main__":
    save_rates()
