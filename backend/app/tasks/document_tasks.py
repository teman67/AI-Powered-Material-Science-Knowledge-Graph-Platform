from app.tasks.celery_app import celery_app


@celery_app.task(name="app.tasks.process_document_task")
def process_document_task(document_id: int) -> dict[str, object]:
    from app.db.session import SessionLocal
    from app.services.document_pipeline import process_document_ingestion

    db = SessionLocal()
    try:
        return process_document_ingestion(document_id=document_id, db=db)
    finally:
        db.close()
