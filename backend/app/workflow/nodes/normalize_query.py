from app.workflow.rag_state import RAGState


async def normalize_query(state: RAGState) -> RAGState:
    return {"query": state["question"]}
