from app.tasks import dispatch
from types import ModuleType
import sys


class DummyTask:
    called = False

    @classmethod
    def delay(cls, document_id: int) -> None:
        cls.called = document_id > 0


def test_enqueue_document_processing_returns_false_when_disabled(monkeypatch) -> None:
    class DummySettings:
        document_processing_use_celery = False

    monkeypatch.setattr(dispatch, "get_settings", lambda: DummySettings())

    assert dispatch.enqueue_document_processing(1) is False


def test_enqueue_document_processing_dispatches_task(monkeypatch) -> None:
    class DummySettings:
        document_processing_use_celery = True

    dummy_module = ModuleType("app.tasks.document_tasks")
    dummy_module.process_document_task = DummyTask

    monkeypatch.setattr(dispatch, "get_settings", lambda: DummySettings())
    monkeypatch.setitem(sys.modules, "app.tasks.document_tasks", dummy_module)

    assert dispatch.enqueue_document_processing(10) is True
    assert DummyTask.called is True
