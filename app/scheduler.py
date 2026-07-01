from apscheduler.schedulers.background import BackgroundScheduler

from app.services.no_show_service import cancel_no_shows

_scheduler = BackgroundScheduler(timezone="UTC")


def start_scheduler() -> None:
    _scheduler.add_job(
        cancel_no_shows,
        trigger="interval",
        minutes=1,
        id="cancel_no_shows",
        replace_existing=True,
        misfire_grace_time=30, 
    )
    _scheduler.start()


def stop_scheduler() -> None:
    if _scheduler.running:
        _scheduler.shutdown(wait=False)
