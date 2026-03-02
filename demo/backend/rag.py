"""
RAG pipeline — builds a retriever tool backed by an IT Help Desk knowledge base.

Uses FAISS + NVIDIA embeddings + NVIDIA reranking, exposed as a single
LangChain tool that the Deep Agent can call.
"""

import os

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_community.vectorstores import FAISS
from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings, NVIDIARerank
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_classic.retrievers import ContextualCompressionRetriever
from langchain_core.tools.retriever import create_retriever_tool

# ── Config ────────────────────────────────────────────────────────────────────

DATA_DIR = os.path.join(os.path.dirname(__file__), "data", "it-knowledge-base")
CHUNK_SIZE = 800
CHUNK_OVERLAP = 120
EMBEDDING_MODEL = "nvidia/llama-3.2-nv-embedqa-1b-v2"
RERANK_MODEL = "nvidia/llama-3.2-nv-rerankqa-1b-v2"

# ── Lazy singleton ────────────────────────────────────────────────────────────

_retriever_tool = None


def get_retriever_tool():
    """Return the IT knowledge-base retriever tool, building it on first call."""
    global _retriever_tool
    if _retriever_tool is not None:
        return _retriever_tool

    if not os.path.isdir(DATA_DIR):
        print(f"[RAG] Knowledge base directory not found: {DATA_DIR}")
        return None

    print("[RAG] Building IT knowledge-base retriever ...")

    # 1. Load documents
    loader = DirectoryLoader(DATA_DIR, glob="**/*.md", loader_cls=TextLoader)
    docs = loader.load()
    print(f"[RAG]   Loaded {len(docs)} documents")

    # 2. Chunk
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    chunks = splitter.split_documents(docs)
    print(f"[RAG]   Split into {len(chunks)} chunks")

    # 3. Embed + store in FAISS
    embeddings = NVIDIAEmbeddings(model=EMBEDDING_MODEL, truncate="END")
    vectordb = FAISS.from_documents(chunks, embeddings)
    print("[RAG]   FAISS vector store ready")

    # 4. Retriever with reranking
    base_retriever = vectordb.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 6},
    )
    reranker = NVIDIARerank(model=RERANK_MODEL)
    retriever = ContextualCompressionRetriever(
        base_retriever=base_retriever,
        base_compressor=reranker,
    )

    # 5. Wrap as tool
    _retriever_tool = create_retriever_tool(
        retriever,
        name="it_knowledge_base",
        description=(
            "Search the internal IT Help Desk knowledge base for company IT policies "
            "and procedures including password resets, VPN access, software installation, "
            "hardware refresh, HPC cluster access, security incident reporting, and more."
        ),
    )
    print("[RAG] Retriever tool ready: it_knowledge_base")
    return _retriever_tool
