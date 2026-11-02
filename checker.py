import json
import os
import sys
from pathlib import Path
from typing import Any

import requests

PRODUCT_URL = "https://store.palantir.com/products/grey-overdye-tonal-chevron-t-shirt"
PRODUCT_JSON_URL = PRODUCT_URL + ".js"
TARGET_SIZE = "M"
STATE_FILE = Path("state.json")


def normalize_size(value: str) -> str:
    return value.strip().upper()


def fetch_product() -> dict[str, Any]:
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; [REDACTED]StockMonitor/1.0)",
        "Accept": "application/json,text/javascript,*/*;q=0.8",
    }
    response = requests.get(PRODUCT_JSON_URL, headers=headers, timeout=20)
    response.raise_for_status()
    return response.json()


def find_variant(product: dict[str, Any], target_size: str) -> dict[str, Any]:
    wanted = normalize_size(target_size)
    variants = product.get("variants") or []

    matches = []
    for variant in variants:
        candidates = [
            str(variant.get("title", "")),
            str(variant.get("option1", "")),
            str(variant.get("option2", "")),
            str(variant.get("option3", "")),
        ]
        if any(normalize_size(v) == wanted for v in candidates if v):
            matches.append(variant)

    if not matches:
        available_titles = [str(v.get("title", "")) for v in variants]
        raise RuntimeError(
            f"Could not find size {target_size!r}. "
            f"Variants returned by store: {available_titles}"
        )

    exact = [
        v for v in matches
        if normalize_size(str(v.get("title", ""))) == wanted
    ]
    if len(exact) == 1:
        return exact[0]

    return matches[0]


def load_previous_state() -> dict[str, Any] | None:
    if not STATE_FILE.exists():
        return None
    try:
        return json.loads(STATE_FILE.read_text())
    except Exception:
        return None


def save_state(available: bool, variant: dict[str, Any]) -> None:
    payload = {
        "available": available,
        "variant_id": variant.get("id"),
        "variant_title": variant.get("title"),
    }
    STATE_FILE.write_text(json.dumps(payload, indent=2) + "\n")


def send_telegram(message: str) -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    if not token or not chat_id:
        raise RuntimeError(
            "Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID GitHub secret."
        )

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    response = requests.post(
        url,
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

    previous = load_previous_state()
    previous_available = None if previous is None else bool(previous.get("available"))
    should_alert = previous_available is False and available is True

    if should_alert:
        send_telegram(
            "🚨 [REDACTED] RESTOCK\n\n"
            "Grey Overdye Tonal Chevron T-Shirt\n"
            "Size: Medium (M)\n"
            "Status: IN STOCK\n\n"
            f"{PRODUCT_URL}"
        )
        print("Telegram restock alert sent.")
    elif previous is None:
        print("First run: baseline state recorded. No restock alert sent.")
    else:
        print("No restock transition. No Telegram alert sent.")

    save_state(available, variant)
    return 0


if __name__ == "__main__":
    sys.exit(main())
