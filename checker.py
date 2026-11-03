import os
import sys
from typing import Any

import requests

PRODUCT_URL = "https://store.palantir.com/products/lightweight-chore-coat-black"
PRODUCT_JSON_URL = PRODUCT_URL + ".js"
TARGET_SIZE = "M"


def normalize_size(value: str) -> str:
    return value.strip().upper()


def fetch_product() -> dict[str, Any]:
    response = requests.get(
        PRODUCT_JSON_URL,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; StockMonitor/1.0)",
            "Accept": "application/json,text/javascript,*/*;q=0.8",
        },
        timeout=20,
    )
    response.raise_for_status()
    return response.json()


def find_variant(product: dict[str, Any], target_size: str) -> dict[str, Any]:
    wanted = normalize_size(target_size)
    variants = product.get("variants") or []

    for variant in variants:
        values = [
            variant.get("title"),
            variant.get("option1"),
            variant.get("option2"),
            variant.get("option3"),
        ]
        if any(
            value is not None and normalize_size(str(value)) == wanted
            for value in values
        ):
            return variant

    titles = [str(v.get("title", "")) for v in variants]
    raise RuntimeError(
        f"Could not find size {target_size!r}. Variants returned: {titles}"
    )


def send_telegram(message: str) -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()

    if not token or not chat_id:
        raise RuntimeError(
            "Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID environment variable."
        )

    response = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": message,
            "disable_web_page_preview": False,
        },
        timeout=20,
    )
    response.raise_for_status()

    data = response.json()
    if not data.get("ok"):
        raise RuntimeError(f"Telegram API returned an error: {data}")


def main() -> int:
    product = fetch_product()
    variant = find_variant(product, TARGET_SIZE)
    available = bool(variant.get("available"))

    print(f"Product: {product.get('title')}")
    print(f"Target size: {TARGET_SIZE}")
    print(f"Variant: {variant.get('title')}")
    print(f"Variant ID: {variant.get('id')}")
    print(f"Available: {available}")

    if available:
        send_telegram(
            "🚨 [REDACTED] RESTOCK\n\n"
            "Lightweight Chore Coat Black\n"
            "Size: Medium (M)\n"
            "Status: IN STOCK\n\n"
            f"{PRODUCT_URL}"
        )
        print("Telegram in-stock alert sent.")
    else:
        print("Medium is out of stock. No Telegram alert sent.")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
