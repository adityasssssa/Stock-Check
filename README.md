# [REDACTED] Stock Monitor

Small Python stock monitor for the **Lightweight Chore Coat Black** in **Medium (M)**.

It is designed to run on an always-on Linux VM. If Medium is in stock, it sends a Telegram alert every time the checker runs.

## What it does

- Checks the exact Medium variant
- Sends a Telegram message when Medium is available
- Sends no message when Medium is sold out
- Intended to run every 5 minutes with systemd
- Does not use GitHub Actions

## Files

- `checker.py` — stock check and Telegram alert
- `requirements.txt` — Python dependency
- `stock-check.service` — systemd service
- `stock-check.timer` — runs the service every 5 minutes

## VM setup

Clone the repo:

```bash
git clone https://github.com/adityasssssa/Stock-Check.git
cd Stock-Check
```

Install Python dependencies:

```bash
sudo apt update
sudo apt install -y python3 python3-venv git
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Create the Telegram environment file:

```bash
sudo nano /etc/stock-check.env
```

Add:

```text
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN
TELEGRAM_CHAT_ID=YOUR_CHAT_ID
```

Protect it:

```bash
sudo chmod 600 /etc/stock-check.env
```

Install the systemd files:

```bash
sudo cp stock-check.service /etc/systemd/system/
sudo cp stock-check.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now stock-check.timer
```

Check that the timer is active:

```bash
systemctl status stock-check.timer
```

Run an immediate test:

```bash
sudo systemctl start stock-check.service
```

View recent logs:

```bash
journalctl -u stock-check.service -n 50 --no-pager
```

## Updating the bot

From the repo folder:

```bash
git pull
.venv/bin/pip install -r requirements.txt
```

The timer will use the updated code on the next run.

## Security

Do not put the Telegram bot token in GitHub. Keep it only in `/etc/stock-check.env` on the VM.
