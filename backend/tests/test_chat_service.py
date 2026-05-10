from app.api.schemas.chat import ChatContext, ChatGraphContext
from app.services.chat_service import build_answer


def test_build_answer_includes_text_and_graph_evidence() -> None:
    text_contexts = [
        ChatContext(chunk_id=1, document_id=1, score=0.91, excerpt="MoS2 shows high mobility in thin films."),
    ]
    graph_contexts = [
        ChatGraphContext(source="MoS2", relation="HAS_PROPERTY", target="carrier mobility"),
    ]

    answer = build_answer("What makes MoS2 useful?", text_contexts, graph_contexts)

    assert "Evidence 1" in answer
    assert "Graph Evidence 1" in answer
    assert "MoS2 -[HAS_PROPERTY]-> carrier mobility" in answer


def test_build_answer_handles_no_context() -> None:
    answer = build_answer("Any data?", [], [])
    assert "No relevant information was found" in answer
