import os
import csv
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


def get_app_id() -> str:
    app_id = os.getenv("OPENEXCHANGERATES_APP_ID")
    if not app_id:
        raise RuntimeError(
            "Missing OPENEXCHANGERATES_APP_ID. Add it in GitHub repo Settings → Secrets and variables → Actions."
        )
    return app_id


def get_openexchangerates_data() -> dict:
    app_id = get_app_id()
    url = "https://openexchangerates.org/api/latest.json"
    params = {
        "app_id": app_id,
        "symbols": "CNY,GBP,EUR",
    }

    response = requests.get(url, params=params, timeout=20)
    response.raise_for_status()
    data = response.json()

    if "rates" not in data:
        raise RuntimeError(f"Unexpected API response: {data}")

    return data


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
    data = get_openexchangerates_data()
    rates = data["rates"]

    # Open Exchange Rates free plan is USD-based
    usd_cny_market = float(rates["CNY"])
    usd_gbp_market = float(rates["GBP"])
    usd_eur_market = float(rates["EUR"])

    gbp_usd_market = 1 / usd_gbp_market
    eur_usd_market = 1 / usd_eur_market

    gbp_usd_paypal_est = estimate_paypal_rate_from_market(
        gbp_usd_market, PAYPAL_CN_OTHER_CONVERSION_SPREAD
    )
    eur_usd_paypal_est = estimate_paypal_rate_from_market(
        eur_usd_market, PAYPAL_CN_OTHER_CONVERSION_SPREAD
    )

    row = [
        get_beijing_hour_label(),
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
