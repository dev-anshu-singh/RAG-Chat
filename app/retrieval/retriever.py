from langchain_classic.retrievers.contextual_compression import ContextualCompressionRetriever
from langchain_cohere import CohereRerank
from langchain_community.vectorstores import Chroma

from app.core.config import settings
from app.core.llm import get_embeddings


def get_reranking_retriever(base_retriever):
    compressor = CohereRerank(
        cohere_api_key=settings.cohere_api_key,
        model="rerank-english-v3.0",
        top_n=6
    )

    compression_retriever = ContextualCompressionRetriever(
        base_compressor=compressor,
        base_retriever=base_retriever
    )

    return compression_retriever


def get_rag_retriever():
    embeddings = get_embeddings()

    vectorstore = Chroma(
        persist_directory=settings.chroma_persist_dir,
        embedding_function=embeddings
    )

    base_retriever = vectorstore.as_retriever(search_kwargs={"k": 30})

    final_retriever = get_reranking_retriever(base_retriever)

    return final_retriever