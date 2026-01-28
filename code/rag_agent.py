"""
RAG Agent with MCP and Skills

This agent combines:
1. RAG - Knowledge base retrieval for IT help desk
2. MCP - Web search via Tavily for current information  
3. Skills - Dynamic expertise loading for specialized tasks
"""

import logging
import os
from pathlib import Path

from langchain_classic.retrievers import ContextualCompressionRetriever
from langchain_classic.text_splitter import RecursiveCharacterTextSplitter
from langchain_classic.tools.retriever import create_retriever_tool
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_community.vectorstores import FAISS
from langchain_core.tools import tool
from langchain_nvidia_ai_endpoints import ChatNVIDIA, NVIDIAEmbeddings, NVIDIARerank
from langgraph.prebuilt import create_react_agent
from tavily import TavilyClient

_LOGGER = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION
# =============================================================================

# Data Ingestion Configuration
DATA_DIR = Path(__file__).parent.parent / "data" / "it-knowledge-base"
SKILLS_DIR = Path(__file__).parent.parent / "skills"
CHUNK_SIZE = 800
CHUNK_OVERLAP = 120

# Model Configuration
LLM_MODEL = "nvidia/llama-3.3-nemotron-super-49b-v1"
RETRIEVER_RERANK_MODEL = "nvidia/llama-3.2-nv-rerankqa-1b-v2"
RETRIEVER_EMBEDDING_MODEL = "nvidia/llama-3.2-nv-embedqa-1b-v2"

# API Keys
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "")

# =============================================================================
# PART 1: RAG - Knowledge Base Retrieval
# =============================================================================

# Read the data
_LOGGER.info(f"Reading knowledge base data from {DATA_DIR}")
data_loader = DirectoryLoader(
    DATA_DIR,
    glob="**/*",
    loader_cls=TextLoader,
    show_progress=True,
)
docs = data_loader.load()

# Split the data into chunks and ingest into FAISS vector database
_LOGGER.info(f"Ingesting {len(docs)} documents into FAISS vector database.")

# EXERCISE 1: Create the text splitter
splitter = ...

chunks = splitter.split_documents(docs)

# EXERCISE 2: Create the embeddings model
embeddings = ...

vectordb = FAISS.from_documents(chunks, embeddings)

# Create a document retriever and reranker
kb_retriever = vectordb.as_retriever(search_type="similarity", search_kwargs={"k": 6})

# EXERCISE 3: Create the reranker
reranker = ...

# Combine those to create the final document retriever
RETRIEVER = ContextualCompressionRetriever(
    base_retriever=kb_retriever,
    base_compressor=reranker,
)

# Create the retriever tool for agentic use
RETRIEVER_TOOL = create_retriever_tool(
    retriever=RETRIEVER,
    name="company_llc_it_knowledge_base",
    description=(
        "Search the internal IT knowledge base for Company LLC IT related questions and policies."
    ),
)

# =============================================================================
# PART 2: MCP - Web Search Tool
# =============================================================================

# EXERCISE 4: Initialize the Tavily client
tavily_client = ...


@tool
def web_search(query: str) -> dict:
    """Search the web for current information on any topic.
    
    Use this when:
    - The knowledge base doesn't have the answer
    - User asks about current events or recent information
    - User needs information beyond internal IT policies
    """
    # EXERCISE 5: Call the Tavily search API
    results = ...
    return results


# =============================================================================
# PART 3: SKILLS - Dynamic Expertise Loading
# =============================================================================

def load_skill(skill_name: str) -> str:
    """Load a skill from the skills directory."""
    skill_path = SKILLS_DIR / skill_name / "SKILL.md"
    if skill_path.exists():
        return skill_path.read_text()
    return f"Skill '{skill_name}' not found."


def list_skills() -> list[str]:
    """List all available skills."""
    if not SKILLS_DIR.exists():
        return []
    return [d.name for d in SKILLS_DIR.iterdir() if d.is_dir() and (d / "SKILL.md").exists()]


@tool
def get_skill(skill_name: str) -> str:
    """Load a specific skill to gain expertise in that area.
    
    Available skills can be found using list_available_skills.
    Skills provide specialized instructions for tasks like code review,
    technical writing, etc.
    """
    # EXERCISE 6: Load the skill
    return ...


@tool
def list_available_skills() -> list[str]:
    """List all available skills that can be loaded.
    
    Returns a list of skill names. Use get_skill(name) to load one.
    """
    # EXERCISE 7: Return the list of skills
    return ...


# =============================================================================
# AGENT SETUP
# =============================================================================

# EXERCISE 8: Define the LLM model
llm = ...

# Define the system prompt with all capabilities
SYSTEM_PROMPT = """You are an IT help desk support agent with enhanced capabilities.

## Your Tools

1. **company_llc_it_knowledge_base** - Search internal IT policies and procedures
   - Use for: Password resets, VPN setup, software installation, etc.
   - Cite with [KB]

2. **web_search** - Search the web for current information
   - Use for: Questions beyond internal policies, current events, external resources
   - Cite with [Web]

3. **list_available_skills** - See what specialized skills you can load
   - Use when: User needs help with a specialized task

4. **get_skill** - Load a skill to gain expertise
   - Use when: You need specialized instructions (e.g., code review, technical writing)

## Guidelines

- Try the knowledge base FIRST for IT-related questions
- Use web search when KB doesn't have the answer or for current information
- Load skills when doing specialized tasks
- Always cite your sources: [KB] for knowledge base, [Web] for web results
- Be concise and helpful
"""

# EXERCISE 9: Create the ReAct agent with ALL tools
AGENT = ...
