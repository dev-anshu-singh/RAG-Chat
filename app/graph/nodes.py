from langchain_core.messages import SystemMessage, HumanMessage
from app.core.llm import get_chat_llm
from app.retrieval.retriever import get_rag_retriever


def retrieve_node(state):
    question = state["question"]
    retriever = get_rag_retriever()
    docs = retriever.invoke(question)
    return {"documents": docs}


def generate_node(state):
    question = state["question"]
    documents = state["documents"]
    messages = state.get("messages", [])

    context = "\n\n".join(doc.page_content for doc in documents)

    system_prompt = SystemMessage(
        content=f"You are a helpful assistant. Use the following context to answer the question.\n\nContext:\n{context}"
    )

    human_msg = HumanMessage(content=question)

    full_conversation = [system_prompt] + messages + [human_msg]

    # 5. Call the LLM
    llm = get_chat_llm()
    response = llm.invoke(full_conversation)

    # 6. Return the answer AND append the new messages to the state
    return {
        "answer": response.content,
        "messages": [human_msg, response]  # LangGraph will automatically append these!
    }