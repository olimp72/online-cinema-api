from celery import Celery

celery_app = Celery(
    "online_cinema",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

celery_app.conf.beat_schedule = {
    "clean-expired-activation-tokens": {
        "task": "app.tasks.tokens.delete_expired_tokens",
        "schedule": 3600.0,
    },
}
celery_app.conf.timezone = "UTC"
