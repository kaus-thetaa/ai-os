from pathlib import Path
import logging
logging.getLogger("pypdf").setLevel(logging.ERROR)

import pypdf
import docx

import file_scanner
import vector_store
import config


class KnowledgeBaseError(Exception):
    pass


def read_pdf_content(file_path: str) -> str:
    # extracts text from every page of a pdf and joins it together
    file = Path(file_path)

    if not file.exists():
        raise KnowledgeBaseError(f"'{file_path}' does not exist")

    try:
        reader = pypdf.PdfReader(str(file))
        pages_text = []

        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages_text.append(text)

        return "\n".join(pages_text)

    except Exception as error:
        raise KnowledgeBaseError(f"failed to read pdf '{file_path}': {error}")


def read_docx_content(file_path: str) -> str:
    # extracts text from every paragraph in a docx file
    file = Path(file_path)

    if not file.exists():
        raise KnowledgeBaseError(f"'{file_path}' does not exist")

    try:
        document = docx.Document(str(file))
        paragraphs_text = [p.text for p in document.paragraphs if p.text.strip()]
        return "\n".join(paragraphs_text)

    except Exception as error:
        raise KnowledgeBaseError(f"failed to read docx '{file_path}': {error}")


def read_any_supported_file(file_path: str) -> str:
    # picks the right reader based on file extension
    extension = Path(file_path).suffix.lower()

    if extension == ".pdf":
        return read_pdf_content(file_path)
    elif extension == ".docx":
        return read_docx_content(file_path)
    elif extension in config.SUPPORTED_TEXT_EXTENSIONS:
        try:
            return file_scanner.read_text_file_content(file_path)
        except file_scanner.FileScannerError as error:
            raise KnowledgeBaseError(str(error))
    else:
        raise KnowledgeBaseError(
            f"'{Path(file_path).name}' has unsupported extension '{extension}'"
        )


def build_knowledge_base(folder_path: str, recursive: bool = True) -> dict:
    # scans a folder and indexes every readable file into the vector store
    try:
        all_files = file_scanner.list_files_in_folder(folder_path, recursive=recursive)
    except file_scanner.FileScannerError as error:
        raise KnowledgeBaseError(f"could not scan folder: {error}")

    files_indexed = 0
    files_skipped = 0
    skipped_reasons = []

    batch_ids = []
    batch_texts = []
    batch_metadatas = []

    for file_path in all_files:
        extension = file_path.suffix.lower()

        is_supported = (
            extension == ".pdf"
            or extension == ".docx"
            or extension in config.SUPPORTED_TEXT_EXTENSIONS
        )

        if not is_supported:
            files_skipped += 1
            skipped_reasons.append((file_path.name, f"unsupported extension '{extension}'"))
            continue

        try:
            content = read_any_supported_file(str(file_path))
        except KnowledgeBaseError as error:
            files_skipped += 1
            skipped_reasons.append((file_path.name, str(error)))
            continue

        if len(content.strip()) < 10:
            files_skipped += 1
            skipped_reasons.append((file_path.name, "little or no readable content"))
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
            raise KnowledgeBaseError(f"failed to store indexed files: {error}")

    return {
        "total_files_found": len(all_files),
        "files_indexed": files_indexed,
        "files_skipped": files_skipped,
        "skipped_reasons": skipped_reasons,
    }


if __name__ == "__main__":
    print("knowledge_base.py self-test")
    print("-" * 50)

    print("clearing existing index for a clean test run")
    vector_store.clear_all_items()
    print(f"item count: {vector_store.get_item_count()}")

    print("-" * 50)
    print(f"building knowledge base from: {config.DOWNLOADS_DIR}")

    try:
        result = build_knowledge_base(str(config.DOWNLOADS_DIR), recursive=False)
        print(f"total files found: {result['total_files_found']}")
        print(f"files indexed: {result['files_indexed']}")
        print(f"files skipped: {result['files_skipped']}")

        if result["skipped_reasons"]:
            print("sample of skipped files:")
            for name, reason in result["skipped_reasons"][:5]:
                print(f"  {name}: {reason}")

    except KnowledgeBaseError as error:
        print(f"failed - {error}")
        exit(1)

    print("-" * 50)
    print(f"total items now in vector store: {vector_store.get_item_count()}")

    if result["files_indexed"] > 0:
        print("-" * 50)
        print("testing search on the newly indexed knowledge base")
        search_results = vector_store.search_similar("rocket avionics firmware", max_results=3)
        for rank, item in enumerate(search_results, start=1):
            print(f"  rank {rank}: {item['metadata']['file_name']} (distance: {item['distance']:.4f})")

    print("-" * 50)
    print("knowledge_base.py self-test complete")