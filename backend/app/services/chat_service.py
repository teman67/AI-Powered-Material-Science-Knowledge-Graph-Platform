from app.api.schemas.chat import ChatContext, ChatGraphContext


def build_answer(query: str, contexts: list[ChatContext], graph_contexts: list[ChatGraphContext] | None = None) -> str:
    graph_contexts = graph_contexts or []

    if not contexts and not graph_contexts:
        return "No relevant information was found in indexed documents or graph knowledge for your question."

    top_contexts = contexts[:3]
    text_snippets = "\n\n".join(
        f"Evidence {index + 1}: {context.excerpt}" for index, context in enumerate(top_contexts)
    )

    graph_snippets = "\n".join(
        f"Graph Evidence {index + 1}: {fact.source} -[{fact.relation}]-> {fact.target}"
        for index, fact in enumerate(graph_contexts[:5])
    )

    sections: list[str] = []
    if text_snippets:
        sections.append(text_snippets)
    if graph_snippets:
        sections.append(graph_snippets)

    assembled_evidence = "\n\n".join(sections)

    return (
        f"For your question: '{query}', the platform found these relevant passages. "
        "You can use them as the grounding context for a final scientific answer.\n\n"
        f"{assembled_evidence}"
    )
