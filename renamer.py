import re
from pathlib import Path
import file_scanner
import llm_engine
import config


class RenamerError(Exception):

    pass

MAX_CHARACTERS_FOR_RENAME_CONTEXT = 3000
WINDOWS_ILLEGAL_FILENAME_CHARACTERS = r'<>:"/\|?*'

WINDOWS_RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
    "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9",
}


MAX_FILENAME_LENGTH = 80



def sanitize_filename(suggested_name: str) -> str:

    name = suggested_name.strip()

    for illegal_char in WINDOWS_ILLEGAL_FILENAME_CHARACTERS:
        name = name.replace(illegal_char, " ")
    name = re.sub(r"\s+", " ", name).strip()

    name = name.rstrip(". ")


    if len(name) > MAX_FILENAME_LENGTH:
        name = name[:MAX_FILENAME_LENGTH].rsplit(" ", 1)[0]

    if not name:
        raise RenamerError(
            "The suggested filename was empty after removing invalid "
            "characters. Try renaming this file manually."
        )

    if name.upper() in WINDOWS_RESERVED_NAMES:
     
        name = f"{name}_file"

    return name


def suggest_filename(file_path: str) -> str:

    file = Path(file_path)
    file_type = file_scanner.classify_file_type(file_path)

    if file_type != "text":
        raise RenamerError(
            f"Cannot suggest a name for '{file.name}' — it is a "
            f"'{file_type}' file. Only plain text formats are "
            f"supported for content-based renaming at this stage."
        )

    try:
        content = file_scanner.read_text_file_content(file_path)
    except file_scanner.FileScannerError as error:
        raise RenamerError(f"Could not read file to suggest a name: {error}")

    if len(content.strip()) < 10:
        raise RenamerError(
            f"'{file.name}' has little or no readable content — "
            f"cannot determine a meaningful name from it."
        )

    content_to_send = content[:MAX_CHARACTERS_FOR_RENAME_CONTEXT]

    prompt = (
        f"Based on the following file content, suggest a short, "
        f"clear, descriptive filename that reflects what this file "
        f"actually contains. Use lowercase words separated by "
        f"underscores. Do NOT include a file extension. Do NOT "
        f"include any explanation — respond with ONLY the suggested "
        f"filename itself, nothing else.\n\n"
        f"Current filename: {file.stem}\n\n"
        f"Content:\n{content_to_send}"
    )

    system_instruction = (
        "You are a file renaming assistant. You respond with ONLY a "
        "short filename in lowercase_with_underscores format, no "
        "extension, no explanation, no punctuation other than "
        "underscores."
    )

    try:
        raw_suggestion = llm_engine.ask_llm(prompt, system_instruction=system_instruction)
    except llm_engine.LLMConnectionError as error:
        raise RenamerError(f"Failed to generate filename suggestion: {error}")

    
    cleaned_suggestion = raw_suggestion.strip().strip('"').strip("'").strip(".")

# only take the first line, in case the model rambled or listed options
    cleaned_suggestion = cleaned_suggestion.splitlines()[0].strip()

# only take the first word-group before any accidental extra filename got appended
    cleaned_suggestion = cleaned_suggestion.split(".txt")[0].split(".html")[0].split(".pdf")[0].split(".docx")[0].split(".md")[0].split(".csv")[0]

    sanitized_name = sanitize_filename(cleaned_suggestion)

# strip the original extension if the model echoed it back despite instructions
    original_extension = file.suffix.lower()
    if sanitized_name.lower().endswith(original_extension):
        sanitized_name = sanitized_name[: -len(original_extension)]

    return f"{sanitized_name}{original_extension}"

def rename_file(file_path: str, new_filename: str) -> str:

    source = Path(file_path)

    if not source.exists():
        raise RenamerError(f"Cannot rename — '{file_path}' does not exist.")

    if not new_filename or not new_filename.strip():
        raise RenamerError("Cannot rename — the new filename is empty.")

    destination = source.parent / new_filename

   
    if destination.exists():
        raise RenamerError(
            f"Cannot rename '{source.name}' to '{new_filename}' — a "
            f"file with that name already exists in "
            f"'{source.parent}'. Choose a different name or handle "
            f"the collision first."
        )

    try:
        source.rename(destination)
        return str(destination)
    except OSError as error:
        raise RenamerError(f"Failed to rename '{source.name}': {error}")


def suggest_and_rename(file_path: str) -> dict:
    
    original_path = str(Path(file_path).resolve())
    original_name = Path(file_path).name

    suggested_name = suggest_filename(file_path)
    new_path = rename_file(file_path, suggested_name)

    return {
        "original_path": original_path,
        "new_path": new_path,
        "original_name": original_name,
        "new_name": suggested_name,
    }


#selftest of the file by ai code
if __name__ == "__main__":
    import shutil
    import tempfile

    print("renamer.py self-test")
    print("-" * 50)

    print("Checking Ollama connection before running tests...")
    if not llm_engine.is_ollama_available():
        print("FAILED — Ollama is not reachable. Start Ollama and try again.")
        exit(1)
    print("OK — Ollama is reachable.")

    print("-" * 50)
    print("Testing sanitize_filename() with problematic inputs...")
    test_cases = [
        ("normal_name", "normal_name"),
        ("name:with<illegal>chars", "name with illegal chars"),
        ("CON", "CON_file"),
        ("  spaced out name  ", "spaced out name"),
        ("trailing.dot.", "trailing.dot"),
    ]
    for raw, expected in test_cases:
        result = sanitize_filename(raw)
        status = "OK" if result == expected else f"MISMATCH (expected '{expected}')"
        print(f"  '{raw}' -> '{result}' [{status}]")

    print("-" * 50)
    print("Creating a temporary test file with clear, identifiable content...")

    # We create our OWN test file in a temp folder rather than
    # touching any of your real files — this makes the test fully
    # safe to run repeatedly without any risk to your actual data.
    temp_dir = Path(tempfile.mkdtemp(prefix="aios_renamer_test_"))
    test_file = temp_dir / "untitled_document_1.txt"
    test_file.write_text(
        "Meeting notes from the ThrustMIT avionics team sync on "
        "July 12th. Discussed STM32 migration timeline and firmware "
        "test plan for the next flight computer revision.",
        encoding="utf-8",
    )
    print(f"Created test file: {test_file}")

    print("-" * 50)
    print("Testing suggest_filename()...")
    try:
        suggested_name = suggest_filename(str(test_file))
        print(f"Original name: {test_file.name}")
        print(f"Suggested name: {suggested_name}")
    except RenamerError as error:
        print(f"FAILED — {error}")
        shutil.rmtree(temp_dir, ignore_errors=True)
        exit(1)

    print("-" * 50)
    print("Testing suggest_and_rename() (full end-to-end rename)...")
    try:
        result = suggest_and_rename(str(test_file))
        print(f"Original: {result['original_name']}")
        print(f"Renamed to: {result['new_name']}")
        print(f"New full path: {result['new_path']}")

        if Path(result["new_path"]).exists():
            print("OK — renamed file exists on disk at the new path.")
        else:
            print("WARNING — renamed file was not found at the expected path.")

    except RenamerError as error:
        print(f"FAILED — {error}")
        shutil.rmtree(temp_dir, ignore_errors=True)
        exit(1)

    print("-" * 50)
    print("Testing collision protection...")
    try:
        # Create a second file, then try to rename it to the SAME
        # name as the file we already renamed above — this should
        # be safely blocked, not silently overwrite.
        second_file = temp_dir / "another_file.txt"
        second_file.write_text("Unrelated content.", encoding="utf-8")
        rename_file(str(second_file), Path(result["new_path"]).name)
        print("WARNING — collision was not blocked as expected.")
    except RenamerError:
        print("OK — rename correctly blocked due to filename collision.")

    print("-" * 50)
    print("Cleaning up temporary test files...")
    shutil.rmtree(temp_dir, ignore_errors=True)
    print("Cleanup complete.")

    print("-" * 50)
    print("renamer.py self-test complete.")