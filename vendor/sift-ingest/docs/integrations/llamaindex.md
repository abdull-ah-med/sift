# LlamaIndex Integration

Use LongParser as a reader in any LlamaIndex pipeline.

## Install

```bash
pip install "longparser[llamaindex]"
```

## Reader

```python
from longparser.integrations.llamaindex import LongParserReader

reader = LongParserReader(chunk_max_tokens=512)
nodes = reader.load_data(file="report.pdf")
# Returns List[llama_index.core.schema.TextNode]
```

Each node includes:
- `text` — chunk content
- `metadata["chunk_id"]` — unique ID
- `metadata["page_numbers"]` — source pages
- `metadata["chunk_type"]` — type of chunk

## Build a VectorStoreIndex

```python
from llama_index.core import VectorStoreIndex
from longparser.integrations.llamaindex import LongParserReader

nodes = LongParserReader().load_data(file="report.pdf")
index = VectorStoreIndex(nodes)

query_engine = index.as_query_engine()
response = query_engine.query("What are the key findings?")
print(response)
```

## With Persistent Storage

```python
from llama_index.core import StorageContext, load_index_from_storage
from llama_index.core.storage.docstore import SimpleDocumentStore

storage_context = StorageContext.from_defaults()
index = VectorStoreIndex(nodes, storage_context=storage_context)
index.storage_context.persist("./index_store")
```
