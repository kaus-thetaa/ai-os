import os
os.environ["ANONYMIZED_TELEMETRY"] = "False"
import logging
logging.getLogger("chromadb.telemetry.product.posthog").setLevel(logging.CRITICAL)
import chromadb
import config
import embeddings_engine

class VectorStoreError(Exception):
    pass


#database client
config.ensure_app_directories_exist()

try:

    _client = chromadb.PersistentClient(
        path=str(config.VECTOR_DB_DIR),
        settings=chromadb.Settings(anonymized_telemetry=False),
    )

    _collection = _client.get_or_create_collection(
        name=config.CHROMA_COLLECTION_NAME
    )
except Exception as error:
    _client = None
    _collection = None
    _init_error = error
else:
    _init_error = None


def _ensure_database_ready() -> None:
  
    if _collection is None:
        raise VectorStoreError(
            f"The vector database failed to initialize at "
            f"{config.VECTOR_DB_DIR}. Original error: {_init_error}"
        )


def add_item(item_id: str, text: str, metadata: dict) -> None:
   
    _ensure_database_ready()

    if not item_id or not item_id.strip():
        raise VectorStoreError("add_item() requires a non-empty item_id.")

    if not text or not text.strip():
        raise VectorStoreError("add_item() requires non-empty text.")

    try:
        # convert the text into a vector using our embeddings engine
        vector = embeddings_engine.embed_text(text)

        _collection.add(
            ids=[item_id],
            embeddings=[vector.tolist()],
            documents=[text.strip()],
            metadatas=[metadata],
        )
    except embeddings_engine.EmbeddingError as error:
        raise VectorStoreError(f"Failed to embed text for storage: {error}")
    except Exception as error:
        raise VectorStoreError(f"Failed to add item to vector database: {error}")



def add_items_batch(item_ids: list[str], texts: list[str], metadatas: list[dict]) -> None:
 
    _ensure_database_ready()

    if not (len(item_ids) == len(texts) == len(metadatas)):
        raise VectorStoreError(
            f"add_items_batch() requires item_ids, texts, and metadatas "
            f"to all be the same length. Got {len(item_ids)} ids, "
            f"{len(texts)} texts, {len(metadatas)} metadatas."
        )

    if not item_ids:
        raise VectorStoreError("add_items_batch() was called with empty lists.")

    try:
   
        vectors = embeddings_engine.embed_texts(texts)

        _collection.add(
            ids=item_ids,
            embeddings=vectors.tolist(),
            documents=[text.strip() for text in texts],
            metadatas=metadatas,
        )
    except embeddings_engine.EmbeddingError as error:
        raise VectorStoreError(f"Failed to embed text batch for storage: {error}")
    except Exception as error:
        raise VectorStoreError(f"Failed to add item batch to vector database: {error}")


def search_similar(query_text: str, max_results: int = 10) -> list[dict]:

    _ensure_database_ready()

    if not query_text or not query_text.strip():
        raise VectorStoreError("search_similar() requires a non-empty query_text.")

    try:
        query_vector = embeddings_engine.embed_text(query_text)

  
        item_count = _collection.count()
        if item_count == 0:
           
            return []

        effective_max_results = min(max_results, item_count)

        results = _collection.query(
            query_embeddings=[query_vector.tolist()],
            n_results=effective_max_results,
        )

        formatted_results = []
        for i in range(len(results["ids"][0])):
            formatted_results.append({
                "id": results["ids"][0][i],
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i],
            })

        return formatted_results

    except embeddings_engine.EmbeddingError as error:
        raise VectorStoreError(f"Failed to embed search query: {error}")
    except Exception as error:
        raise VectorStoreError(f"Failed to search vector database: {error}")

def delete_item(item_id: str) -> None:
  
    _ensure_database_ready()

    try:
        _collection.delete(ids=[item_id])
    except Exception as error:
        raise VectorStoreError(f"Failed to delete item '{item_id}': {error}")

def get_item_count() -> int:

    _ensure_database_ready()

    try:
        return _collection.count()
    except Exception as error:
        raise VectorStoreError(f"Failed to get item count: {error}")


#clear DB
def clear_all_items() -> None:
  
    _ensure_database_ready()

    try:

        global _collection
        _client.delete_collection(name=config.CHROMA_COLLECTION_NAME)
        _collection = _client.get_or_create_collection(
            name=config.CHROMA_COLLECTION_NAME
        )
    except Exception as error:
        raise VectorStoreError(f"Failed to clear vector database: {error}")



if __name__ == "__main__":
    print("vector_store.py self-test")
    print("-" * 50)

    print(f"Vector database location: {config.VECTOR_DB_DIR}")
    _ensure_database_ready()
    print("OK — vector database is ready.")

    print("-" * 50)
    print("Clearing any existing test data for a clean test run...")
    clear_all_items()
    print(f"Item count after clearing: {get_item_count()}")

    print("-" * 50)
    print("Adding sample items to the database...")
    add_item(
        item_id="C:/fake/2023_tax_return.pdf",
        text="This document contains my 2023 annual tax return and income statements.",
        metadata={"file_name": "2023_tax_return.pdf", "file_type": "pdf"},
    )
    add_item(
        item_id="C:/fake/vacation_photo.jpg",
        text="A photo taken during summer vacation in Italy, showing the coastline.",
        metadata={"file_name": "vacation_photo.jpg", "file_type": "jpg"},
    )
    add_item(
        item_id="C:/fake/budget_meeting_notes.txt",
        text="Notes from the quarterly budget review meeting with the finance team.",
        metadata={"file_name": "budget_meeting_notes.txt", "file_type": "txt"},
    )
    print(f"Item count after adding: {get_item_count()}")

    print("-" * 50)
    print("Searching for: 'income tax documents'")
    results = search_similar("income tax documents", max_results=3)
    for rank, result in enumerate(results, start=1):
        print(f"  Rank {rank}: {result['metadata']['file_name']} "
              f"(distance: {result['distance']:.4f})")

    print("-" * 50)
    if results and results[0]["metadata"]["file_name"] == "2023_tax_return.pdf":
        print("OK — the most relevant result for a tax-related query")
        print("was correctly identified as the tax return document.")
    else:
        print("WARNING — search did not return the expected top result.")

    print("-" * 50)
    print("Testing deletion...")
    delete_item("C:/fake/vacation_photo.jpg")
    print(f"Item count after deleting one item: {get_item_count()}")

    print("-" * 50)
    print("Cleaning up test data...")
    clear_all_items()
    print(f"Item count after final cleanup: {get_item_count()}")

    print("-" * 50)
    print("vector_store.py self-test complete.")