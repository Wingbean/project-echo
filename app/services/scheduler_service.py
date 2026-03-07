# app/services/scheduler_service.py - Background Task Scheduler
import schedule
import time
import threading
from datetime import datetime

from app.utils.helpers import get_current_month_range
from app.services.hosxp_service import sync_data_from_hosxp


def run_sync_job():
    """Scheduled sync job — syncs data from HosXP to SQLite cache."""

    start_date, end_date = get_current_month_range()
    print(f"⏰ Automatic Sync Started: {start_date} to {end_date}")

    try:
        result = sync_data_from_hosxp(start_date, end_date)
        print(f"✅ Automatic Sync Completed. Result: {result.get('status')}")
    except Exception as e:
        print(f"❌ Automatic Sync Failed: {e}")


def run_scheduler():
    """Main scheduler loop — runs in a background thread.

    Configure sync times here.
    """
    # Schedule sync jobs
    schedule.every().day.at("08:00").do(run_sync_job)
    schedule.every().day.at("12:00").do(run_sync_job)
    schedule.every().day.at("16:00").do(run_sync_job)

    print("⏳ Scheduler initialized. Jobs at: 08:00, 12:00, 16:00")

    while True:
        schedule.run_pending()
        time.sleep(60)


def start_scheduler():
    """Start the scheduler in a daemon background thread."""
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    print("✅ Scheduler thread started.")
