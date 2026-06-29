"""
APScheduler setup — nightly penalty cron job.

Jobs:
  - apply_penalties: runs every night at 00:05
  - daily_backup_reminder: logs a reminder at 02:00 (actual backup via shell script)
"""

import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None


def start_scheduler():
    global _scheduler
    if _scheduler and _scheduler.running:
        return

    from app.db.base import SessionLocal
    from app.services.bill_service import apply_penalties_for_all

    _scheduler = BackgroundScheduler(timezone="Asia/Kolkata")

    # ── Nightly penalty job ───────────────────────────────
    def _penalty_job():
        logger.info("[Scheduler] Running nightly penalty calculation...")
        db = SessionLocal()
        try:
            updated = apply_penalties_for_all(db)
            logger.info(f"[Scheduler] Penalty job done — {updated} bills updated")
        except Exception as e:
            logger.error(f"[Scheduler] Penalty job failed: {e}")
        finally:
            db.close()

    _scheduler.add_job(
        _penalty_job,
        trigger=CronTrigger(hour=0, minute=5),
        id="nightly_penalty",
        name="Nightly penalty calculation",
        replace_existing=True,
        misfire_grace_time=3600,   # allow up to 1hr late run
    )

    # ── Backup reminder (placeholder) ─────────────────────
    def _backup_reminder():
        logger.info("[Scheduler] Daily DB backup should be running via pg_dump cron")

    _scheduler.add_job(
        _backup_reminder,
        trigger=CronTrigger(hour=2, minute=0),
        id="backup_reminder",
        replace_existing=True,
    )

    _scheduler.start()
    logger.info("[Scheduler] Started — penalty cron at 00:05 IST daily")


def stop_scheduler():
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("[Scheduler] Stopped")
