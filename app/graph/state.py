from typing import TypedDict, List, Annotated
from langchain_core.documents import Document
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class GraphState(TypedDict):
    question: str
    documents: List[Document]
    answer: str
    messages: Annotated[List[BaseMessage], add_messages]