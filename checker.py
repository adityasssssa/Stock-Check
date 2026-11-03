import json
import os
import sys
from pathlib import Path
from typing import Any

import requests

PRODUCT_URL = "https://store.palantir.com/products/lightweight-chore-coat-black"
PRODUCT_JSON_URL = PRODUCT_URL + ".js"
TARGET_SIZE = "M"
HEALTH_STATE_FILE = Path(__file__).with_name(".monitor_health.json")


class WebsiteBlockedError(RuntimeError):
    pass


def normalize_size(value: str) -> str:
    return value.strip().upper()


def load_health_status() -> str:
    try:
        data = json.loads(HEALTH_STATE_FILE.read_text())
        return str(data.get("status", "healthy"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return "healthy"


def save_health_status(status: str) -> None:
    HEALTH_STATE_FILE.write_text(json.dumps({"status": status}))


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


def notify_site_problem_once(message: str) -> None:
    if load_health_status() != "error":
        send_telegram(message)
    save_health_status("error")


def mark_site_healthy() -> None:
    if load_health_status() == "error":
        send_telegram(
            "✅ STOCK MONITOR RECOVERED\n\n"
            "The store is responding normally again.\n"
            "Monitoring Medium (M) for the Lightweight Chore Coat Black."
        )
    save_health_status("healthy")


def fetch_product() -> dict[str, Any]:
    response = requests.get(
        PRODUCT_JSON_URL,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; StockMonitor/1.0)",
            "Accept": "application/json,text/javascript,*/*;q=0.8",
        },
        timeout=20,
    )

    if response.status_code in (403, 429):
        raise WebsiteBlockedError(
            f"Store returned HTTP {response.status_code}; the monitor may be blocked or rate-limited."
        )

    response.raise_for_status()

    try:
        product = response.json()
    except ValueError as exc:
        raise WebsiteBlockedError(
            "Store returned a non-JSON response; this may be an anti-bot or challenge page."
        ) from exc

    if not isinstance(product, dict) or not product.get("variants"):
        raise WebsiteBlockedError(
            "Store response did not contain expected product variant data."
        )

    return product


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


def check_store() -> tuple[dict[str, Any], dict[str, Any]]:
    try:
        product = fetch_product()
        variant = find_variant(product, TARGET_SIZE)
    except WebsiteBlockedError as exc:
        notify_site_problem_once(
            "⚠️ STOCK MONITOR WARNING\n\n"
            "The store may be blocking or rate-limiting the monitor.\n"
            f"Reason: {exc}\n\n"
            "The bot will keep checking every 5 minutes and will alert you when access recovers."
        )
        raise
    except requests.RequestException as exc:
        notify_site_problem_once(
            "⚠️ STOCK MONITOR WARNING\n\n"
            "The monitor could not reach the store.\n"
            f"Reason: {type(exc).__name__}\n\n"
            "The bot will keep checking every 5 minutes and will alert you when access recovers."
        )
        raise
    except RuntimeError as exc:
        notify_site_problem_once(
            "⚠️ STOCK MONITOR WARNING\n\n"
            "The product page changed or the Medium variant could not be found.\n"
            f"Reason: {exc}\n\n"
            "The bot will keep checking every 5 minutes."
        )
        raise

    mark_site_healthy()
    return product, variant


def main() -> int:
    product, variant = check_store()
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
