
from pathlib import Path
import file_scanner
import vector_store


class SearchEngineError(Exception):

    pass


def index_folder(folder_path: str, recursive: bool = True) -> dict:

    try:
        all_files = file_scanner.list_files_in_folder(folder_path, recursive=recursive)
    except file_scanner.FileScannerError as error:
        raise SearchEngineError(f"Could not index folder: {error}")

    files_indexed = 0
    files_skipped = 0
    skipped_reasons = []

    batch_ids = []
    batch_texts = []
    batch_metadatas = []

    for file_path in all_files:
        file_type = file_scanner.classify_file_type(str(file_path))

        if file_type != "text":
            files_skipped += 1
            skipped_reasons.append((file_path.name, f"file type '{file_type}' not yet indexable"))
            continue

        try:
            content = file_scanner.read_text_file_content(str(file_path))
        except file_scanner.FileScannerError as error:

            files_skipped += 1
            skipped_reasons.append((file_path.name, str(error)))
            continue

        if len(content.strip()) < 10:
            files_skipped += 1
            skipped_reasons.append((file_path.name, "file has little or no readable content"))
            continue

        metadata = file_scanner.get_file_metadata(str(file_path))

        batch_ids.append(metadata["full_path"])
        batch_texts.append(content)
        batch_metadatas.append({
            "file_name": metadata["name"],
            "file_path": metadata["full_path"],
            "extension": metadata["extension"],
            "size_bytes": metadata["size_bytes"],
        })
        files_indexed += 1

    if batch_ids:
        try:
            vector_store.add_items_batch(batch_ids, batch_texts, batch_metadatas)
        except vector_store.VectorStoreError as error:
            raise SearchEngineError(f"Failed to store indexed files: {error}")

    return {
        "total_files_found": len(all_files),
        "files_indexed": files_indexed,
        "files_skipped": files_skipped,
        "skipped_reasons": skipped_reasons,
    }

def search_files(query: str, max_results: int = 10) -> list[dict]:

    try:
        raw_results = vector_store.search_similar(query, max_results=max_results)
    except vector_store.VectorStoreError as error:
        raise SearchEngineError(f"Search failed: {error}")

    formatted_results = []
    for result in raw_results:

        distance = result["distance"]
        relevance_score = 1.0 / (1.0 + distance)

        content = result["text"]
        preview = content[:200].replace("\n", " ").strip()

        formatted_results.append({
            "file_name": result["metadata"]["file_name"],
            "file_path": result["metadata"]["file_path"],
            "extension": result["metadata"]["extension"],
            "relevance_score": round(relevance_score, 4),
            "content_preview": preview,
        })

    return formatted_results

def remove_file_from_index(file_path: str) -> None:

    try:
        resolved_path = str(Path(file_path).resolve())
        vector_store.delete_item(resolved_path)
    except vector_store.VectorStoreError as error:
        raise SearchEngineError(f"Failed to remove '{file_path}' from index: {error}")

def get_index_status() -> dict:
  
    try:
        count = vector_store.get_item_count()
        return {"total_indexed_files": count}
    except vector_store.VectorStoreError as error:
        raise SearchEngineError(f"Failed to get index status: {error}")


if __name__ == "__main__":
    import config

    print("search_engine.py self-test")
    print("-" * 50)

    print("Clearing any existing index data for a clean test run...")
    vector_store.clear_all_items()
    print(f"Index status: {get_index_status()}")

    print("-" * 50)
    print(f"Indexing folder: {config.DOWNLOADS_DIR}")
    print("(This will only index plain text files — .txt, .md, .csv, "
          "etc. PDFs and other document types are skipped for now, "
          "which is expected at this stage of the build.)")

    try:
        index_result = index_folder(str(config.DOWNLOADS_DIR), recursive=False)
        print(f"Total files found: {index_result['total_files_found']}")
        print(f"Files indexed: {index_result['files_indexed']}")
        print(f"Files skipped: {index_result['files_skipped']}")

        if index_result["skipped_reasons"]:
            print("Sample of skipped files:")
            for name, reason in index_result["skipped_reasons"][:5]:
                print(f"  - {name}: {reason}")
    except SearchEngineError as error:
        print(f"FAILED — {error}")
        exit(1)

    print("-" * 50)

    if index_result["files_indexed"] == 0:
        print("No text files were indexed from your Downloads folder,")
        print("so the search test below will be skipped. This is not")
        print("a failure — it just means you don't have plain .txt/.md/")
        print(".csv files directly in Downloads right now. We'll fully")
        print("test search once knowledge_base.py adds PDF/DOCX support.")
    else:
        print("Testing search with a generic query: 'notes'")
        results = search_files("notes", max_results=5)
        if results:
            for rank, result in enumerate(results, start=1):
                print(f"  Rank {rank}: {result['file_name']} "
                      f"(relevance: {result['relevance_score']})")
        else:
            print("No results returned (index may not contain matching content).")

    print("-" * 50)
    print("Testing get_index_status()...")
    status = get_index_status()
    print(f"Total indexed files: {status['total_indexed_files']}")

    print("-" * 50)
    print("search_engine.py self-test complete.")