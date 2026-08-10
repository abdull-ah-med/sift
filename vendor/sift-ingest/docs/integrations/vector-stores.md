# Vector Stores

LongParser supports three vector store backends for the REST server.

## Chroma (Default)

No extra setup required. Uses a local persistent directory.

```bash
LONGPARSER_VECTOR_DB=chroma
LONGPARSER_COLLECTION=my_collection
```

## FAISS

In-memory, high-performance. Best for single-node deployments.

```bash
LONGPARSER_VECTOR_DB=faiss
```

```bash
pip install faiss-cpu
# or
pip install faiss-gpu  # CUDA
```

## Qdrant

Production-grade, distributed. Recommended for multi-tenant deployments.

```bash
# Start Qdrant
docker run -p 6333:6333 qdrant/qdrant

# Configure
LONGPARSER_VECTOR_DB=qdrant
QDRANT_URL=http://localhost:6333
```

```bash
pip install qdrant-client
```

## Switching Between Stores

You can embed the same job into multiple vector stores and search against any index version:

```bash
# Embed into Chroma
POST /jobs/{job_id}/embed
{"vector_db": "chroma", "provider": "openai", "model": "text-embedding-3-small"}

# Embed into Qdrant
POST /jobs/{job_id}/embed
{"vector_db": "qdrant", "provider": "openai", "model": "text-embedding-3-small"}

# Search against a specific index version
POST /search
{"job_id": "...", "query": "...", "index_version": "v1"}
```
