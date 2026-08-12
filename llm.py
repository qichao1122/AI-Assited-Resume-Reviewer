from langchain_ollama import ChatOllama


def get_llm():

    """
    Returns a LangChain chat model instance, or None if it can't be created
    (e.g. Ollama isn't installed/running). Callers should handle the None
    case with a non-LLM fallback so the app still works.
    """
    try:
        llm = ChatOllama(
            model="qwen2.5:7b",
            temperature=0
        )

        return llm
    except Exception:
        return None


