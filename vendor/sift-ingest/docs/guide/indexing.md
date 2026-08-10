# Vector Indexing

After chunking, embed and index your documents for similarity search.

## Supported Vector Stores

| Store | Backend | Notes |
|---|---|---|
| **Chroma** | Local / Server | Default. No extra setup needed. |
| **FAISS** | Local | In-memory, fast, no server. |
| **Qdrant** | Server | Production-grade, scalable. |

## Supported Embedding Providers

| Provider | Models |
|---|---|
| `huggingface` | `BAAI/bge-base-en-v1.5` (default) |
| `openai` | `text-embedding-3-small`, `text-embedding-3-large` |
| `cohere` | `embed-english-v3.0` |

## Embed via REST API

```bash
# After finalizing HITL review:
curl -X POST http://localhost:8000/jobs/{job_id}/embed \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "huggingface",
    "model": "BAAI/bge-base-en-v1.5",
    "vector_db": "chroma",
    "collection_name": "my_docs"
  }'
```

## Search

```bash
curl -X POST http://localhost:8000/search \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "abc123",
    "query": "What is the revenue for Q3?",
    "top_k": 5
  }'
```

## Index Versions

Every embed call creates a new **index version** so you can roll back:

```bash
# List index versions
curl http://localhost:8000/jobs/{job_id} -H "X-API-Key: your-key"

# Search against a specific version
curl -X POST http://localhost:8000/search \
  -d '{"job_id": "abc", "query": "...", "index_version": "v1"}'
```
