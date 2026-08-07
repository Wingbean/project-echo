# app/utils/telegram.py - Send Telegram notifications (e.g. sync job reports)
import shutil

import requests

from app.config import Config


def get_system_status() -> str:
    """Return 'Disk: X% used | RAM: Y% used' for the app's data disk (host's /mnt/data)."""
    disk = shutil.disk_usage(Config.BASE_DIR)
    disk_percent = disk.used / disk.total * 100

    meminfo = {}
    with open("/proc/meminfo") as f:
        for line in f:
            key, value = line.split(":", 1)
            meminfo[key] = int(value.strip().split()[0])  # kB
    ram_percent = (1 - meminfo["MemAvailable"] / meminfo["MemTotal"]) * 100

    return f"Disk: {disk_percent:.1f}% used | RAM: {ram_percent:.1f}% used"


def send_telegram(message: str):
    """Send a Telegram message. No-ops (silently) if bot token/chat id aren't configured."""
    if not Config.TELEGRAM_BOT_TOKEN or not Config.TELEGRAM_CHAT_ID:
        return

    url = f"https://api.telegram.org/bot{Config.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": Config.TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except requests.RequestException as e:
        print(f"⚠️ Telegram send failed: {e}")
