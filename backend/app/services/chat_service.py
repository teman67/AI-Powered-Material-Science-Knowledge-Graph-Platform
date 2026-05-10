from app.api.schemas.chat import ChatContext


def build_answer(query: str, contexts: list[ChatContext]) -> str:
    if not contexts:
        return "No relevant information was found in indexed documents for your question."

    top_contexts = contexts[:3]
    snippets = "\n\n".join(
        f"Evidence {index + 1}: {context.excerpt}" for index, context in enumerate(top_contexts)
    )

    return (
        f"For your question: '{query}', the platform found these relevant passages. "
        "You can use them as the grounding context for a final scientific answer.\n\n"
        f"{snippets}"
    )
