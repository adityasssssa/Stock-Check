# [REDACTED] Telegram Restock Bot

Monitors the **Grey Overdye Tonal Chevron T-Shirt** in **Medium (M)**.

- Product: https://store.palantir.com/products/grey-overdye-tonal-chevron-t-shirt
- Check frequency: every 15 minutes
- Alerts: Telegram
- Runs on: GitHub Actions
- Laptop required: No

## Telegram setup

1. Open Telegram and message **@BotFather**.
2. Send `/newbot`.
3. Follow the prompts and copy the bot token.
4. Open your new bot and send it a message such as `hello`.
5. In a browser, open:

   `https://api.telegram.org/botYOUR_BOT_TOKEN/getUpdates`

6. Find:

   `"chat": {"id": 123456789}`

That number is your Telegram chat ID.

## GitHub setup

Create a GitHub repository and upload all files, including:

`.github/workflows/stock-check.yml`

Then open:

**Settings → Secrets and variables → Actions**

Create these repository secrets:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

Then open:

**Settings → Actions → General → Workflow permissions**

Choose:

**Read and write permissions**

The bot needs this so it can save `state.json` and remember the previous stock state.

## Test Telegram

Open:

**Actions → [REDACTED] Medium Shirt Stock Check → Run workflow**

Turn on:

**Send a Telegram test message instead of checking stock**

Run the workflow.

You should get:

`✅ [REDACTED] stock bot test: Telegram notifications are working.`

## Test the stock checker

Run the workflow again with the test option turned off.

The logs should show:

- Product name
- Target size: M
- Variant ID
- `Available: True` or `Available: False`

The bot reads the exact Medium variant from Shopify's product data.

## Alert behavior

The first stock run records the current state.

After that, Telegram alerts are sent only when Medium changes from:

`False → True`

So it will not spam you every 15 minutes while the shirt stays in stock.

## Security

Never put the Telegram bot token directly in your code or README. Keep it only in GitHub Secrets.
