from app.core.config import get_settings


def enqueue_document_processing(document_id: int) -> bool:
    settings = get_settings()
    if not settings.document_processing_use_celery:
        return False

    try:
        from app.tasks.document_tasks import process_document_task

        process_document_task.delay(document_id)
        return True
    except Exception:
        return False
