import os
import csv
import time
import requests
from datetime import datetime, timezone, timedelta

FILE = "exchange_rates.csv"

EXPECTED_HEADER = [
    "timestamp",
    "USD_CNY_market",
    "GBP_USD_market",
    "EUR_USD_market",
    "GBP_USD_paypal_est_cn",
    "EUR_USD_paypal_est_cn",
]

# PayPal CN public fee page:
# "all other currency conversions" = 2.5%
PAYPAL_CN_OTHER_CONVERSION_SPREAD = 0.025


def get_beijing_hour_label() -> str:
    beijing_tz = timezone(timedelta(hours=8))
    now = datetime.now(beijing_tz).replace(minute=0, second=0, microsecond=0)
    return now.strftime("%Y-%m-%d %H:%M")


def get_api_key() -> str:
    api_key = os.getenv("ALPHAVANTAGE_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Missing ALPHAVANTAGE_API_KEY. Add it in GitHub repo Settings → Secrets and variables → Actions."
        )
    return api_key


def fetch_alpha_rate(from_currency: str, to_currency: str) -> float:
    api_key = get_api_key()
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "CURRENCY_EXCHANGE_RATE",
        "from_currency": from_currency,
        "to_currency": to_currency,
        "apikey": api_key,
    }

    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()

    # Success payload
    if "Realtime Currency Exchange Rate" in data:
        rate_str = data["Realtime Currency Exchange Rate"]["5. Exchange Rate"]
        return float(rate_str)

    # API note / limit / error
    if "Note" in data:
        raise RuntimeError(f"Alpha Vantage limit or note: {data['Note']}")
    if "Information" in data:
        raise RuntimeError(f"Alpha Vantage info: {data['Information']}")
    if "Error Message" in data:
        raise RuntimeError(f"Alpha Vantage error: {data['Error Message']}")

    raise RuntimeError(f"Unexpected Alpha Vantage response: {data}")


def estimate_paypal_rate_from_market(market_rate: float, spread: float) -> float:
    return market_rate * (1 - spread)


def get_file_mode() -> str:
    if not os.path.isfile(FILE):
        return "w"

    with open(FILE, "r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader, None)

    if header != EXPECTED_HEADER:
        return "w"

    return "a"


def save_rates():
    timestamp = get_beijing_hour_label()

    # Add small pauses to reduce chance of hitting short-window limits
    usd_cny_market = fetch_alpha_rate("USD", "CNY")
    time.sleep(15)

    gbp_usd_market = fetch_alpha_rate("GBP", "USD")
    time.sleep(15)

    eur_usd_market = fetch_alpha_rate("EUR", "USD")

    gbp_usd_paypal_est = estimate_paypal_rate_from_market(
        gbp_usd_market, PAYPAL_CN_OTHER_CONVERSION_SPREAD
    )
    eur_usd_paypal_est = estimate_paypal_rate_from_market(
        eur_usd_market, PAYPAL_CN_OTHER_CONVERSION_SPREAD
    )

    row = [
        timestamp,
        f"{usd_cny_market:.6f}",
        f"{gbp_usd_market:.6f}",
        f"{eur_usd_market:.6f}",
        f"{gbp_usd_paypal_est:.6f}",
        f"{eur_usd_paypal_est:.6f}",
    ]

    mode = get_file_mode()

    with open(FILE, mode, newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        if mode == "w":
            writer.writerow(EXPECTED_HEADER)

        writer.writerow(row)

    print("Saved one row to exchange_rates.csv")


if __name__ == "__main__":
    save_rates()
