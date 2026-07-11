
from pathlib import Path
from datetime import datetime
import config

class FileScannerError(Exception):
    pass


def list_files_in_folder(folder_path: str, recursive: bool = False) -> list[Path]:

    folder = Path(folder_path)

    if not folder.exists():
        raise FileScannerError(f"The folder '{folder_path}' does not exist.")

    if not folder.is_dir():
        raise FileScannerError(f"'{folder_path}' exists but is not a folder.")

    try:
        if recursive:
          
            all_items = folder.rglob("*")
        else:
           
            all_items = folder.glob("*")

        files_only = [item for item in all_items if item.is_file()]
        return files_only

    except PermissionError as error:
        raise FileScannerError(
            f"Permission denied while scanning '{folder_path}'. "
            f"Some files or subfolders may require administrator "
            f"access. Original error: {error}"
        )
    except OSError as error:
        raise FileScannerError(
            f"An error occurred while scanning '{folder_path}': {error}"
        )


def get_file_metadata(file_path: str) -> dict:

    file = Path(file_path)

    if not file.exists():
        raise FileScannerError(f"The file '{file_path}' does not exist.")

    if not file.is_file():
        raise FileScannerError(f"'{file_path}' exists but is not a file.")

    try:
     
        file_stats = file.stat()

        return {
            "name": file.name,
            "extension": file.suffix.lower(),
            "size_bytes": file_stats.st_size,
            "modified_date": datetime.fromtimestamp(file_stats.st_mtime),
            "full_path": str(file.resolve()),
        }
    except OSError as error:
        raise FileScannerError(
            f"Failed to read metadata for '{file_path}': {error}"
        )


def classify_file_type(file_path: str) -> str:
 
    extension = Path(file_path).suffix.lower()

    if extension in config.SUPPORTED_TEXT_EXTENSIONS:
        return "text"
    elif extension in config.SUPPORTED_DOCUMENT_EXTENSIONS:
        return "document"
    elif extension in config.IMAGE_EXTENSIONS:
        return "image"
    elif extension in config.VIDEO_EXTENSIONS:
        return "video"
    else:
        return "other"


def read_text_file_content(file_path: str) -> str:

    file = Path(file_path)

    if not file.exists():
        raise FileScannerError(f"The file '{file_path}' does not exist.")

    if not file.is_file():
        raise FileScannerError(f"'{file_path}' exists but is not a file.")

    extension = file.suffix.lower()
    if extension not in config.SUPPORTED_TEXT_EXTENSIONS:
        raise FileScannerError(
            f"'{file_path}' has extension '{extension}', which is not "
            f"a supported plain-text format. Supported extensions: "
            f"{sorted(config.SUPPORTED_TEXT_EXTENSIONS)}"
        )

  
    file_size = file.stat().st_size
    if file_size > config.MAX_READABLE_FILE_SIZE_BYTES:
        raise FileScannerError(
            f"'{file_path}' is {file_size:,} bytes, which exceeds the "
            f"maximum readable size of "
            f"{config.MAX_READABLE_FILE_SIZE_BYTES:,} bytes. This file "
            f"was skipped to avoid loading too much data into memory."
        )

    try:
    
        return file.read_text(encoding="utf-8", errors="replace")
    except OSError as error:
        raise FileScannerError(f"Failed to read '{file_path}': {error}")



def format_file_size(size_bytes: int) -> str:

    size = float(size_bytes)
    for unit in ["bytes", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f} {unit}" if unit != "bytes" else f"{int(size)} {unit}"
        size /= 1024
    return f"{size:.1f} TB"



if __name__ == "__main__":
    print("file_scanner.py self-test")
    print("-" * 50)

    # We test against the user's actual Downloads folder since it's
    # guaranteed to exist on any Windows machine, giving us a
    # realistic test without needing to create fake test files.
    test_folder = str(config.DOWNLOADS_DIR)
    print(f"Testing folder scan on: {test_folder}")

    try:
        files = list_files_in_folder(test_folder, recursive=False)
        print(f"OK — found {len(files)} file(s) in Downloads (non-recursive).")
    except FileScannerError as error:
        print(f"FAILED — {error}")
        exit(1)

    print("-" * 50)

    if len(files) == 0:
        print("Your Downloads folder is empty, so metadata/content tests")
        print("will be skipped. This is not a failure — just nothing to test.")
    else:
        # We test metadata + classification on the first file found,
        # whatever it happens to be.
        sample_file = files[0]
        print(f"Testing metadata on: {sample_file.name}")

        metadata = get_file_metadata(str(sample_file))
        print(f"  Name: {metadata['name']}")
        print(f"  Extension: {metadata['extension']}")
        print(f"  Size: {format_file_size(metadata['size_bytes'])}")
        print(f"  Modified: {metadata['modified_date']}")

        file_type = classify_file_type(str(sample_file))
        print(f"  Classified as: {file_type}")

        print("-" * 50)
        if file_type == "text":
            print(f"Attempting to read text content of {sample_file.name}...")
            try:
                content = read_text_file_content(str(sample_file))
                preview = content[:200].replace("\n", " ")
                print(f"OK — read {len(content)} characters.")
                print(f"Preview: {preview}...")
            except FileScannerError as error:
                print(f"Note: {error}")
        else:
            print(f"Skipping text content read — file type is "
                  f"'{file_type}', not a supported text format.")

    print("-" * 50)
    print("Testing format_file_size() with known values...")
    test_cases = [
        (500, "500 bytes"),
        (2048, "2.0 KB"),
        (5242880, "5.0 MB"),
    ]
    for size_bytes, expected in test_cases:
        result = format_file_size(size_bytes)
        status = "OK" if result == expected else "MISMATCH"
        print(f"  {size_bytes} bytes -> {result} (expected {expected}) [{status}]")

    print("-" * 50)
    print("file_scanner.py self-test complete.")