"""
Configuration - File search tool constants
"""

# File size limits
MAX_FILE_SIZE_MB = 3
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# Token limits
DIRECT_TOKEN_LIMIT = 80_000  # Use direct extraction if ≤80k tokens
MAX_TOKEN_LIMIT = 120_000  # Hard limit (reject documents above this)

# RAG settings
CHUNK_SIZE_TOKENS = 1000
CHUNK_OVERLAP_TOKENS = 100
TOP_K_CHUNKS = 10

# Model settings
EMBEDDING_MODEL = "text-embedding-3-small"
LLM_MODEL = "gpt-4o-mini"  # Used for tiktoken encoding
