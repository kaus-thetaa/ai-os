from pathlib import Path
import file_scanner
import llm_engine
import config

class SummarizerError(Exception):
    
    pass


MAX_CHARACTERS_PER_FILE_FOR_SUMMARY = 6000

MAX_FILES_TO_SUMMARIZE_PER_FOLDER = 20


def summarize_file(file_path: str) -> str:
    
    file_type = file_scanner.classify_file_type(file_path)

    if file_type != "text":
        raise SummarizerError(
            f"Cannot summarize '{Path(file_path).name}' — it is a "
            f"'{file_type}' file. Only plain text formats "
            f"({sorted(config.SUPPORTED_TEXT_EXTENSIONS)}) can be "
            f"summarized at this stage. PDF/DOCX summarization will "
            f"be added once knowledge_base.py includes readers for "
            f"those formats."
        )

    try:
        content = file_scanner.read_text_file_content(file_path)
    except file_scanner.FileScannerError as error:
        raise SummarizerError(f"Could not read file to summarize: {error}")

    if len(content.strip()) < 10:
        raise SummarizerError(
            f"'{Path(file_path).name}' has little or no readable "
            f"content — nothing meaningful to summarize."
        )


    was_truncated = len(content) > MAX_CHARACTERS_PER_FILE_FOR_SUMMARY
    content_to_send = content[:MAX_CHARACTERS_PER_FILE_FOR_SUMMARY]

    truncation_note = (
        " (Note: this is only the first portion of a longer file.)"
        if was_truncated else ""
    )

    prompt = (
        f"Summarize the following file content in 2-4 clear sentences. "
        f"Focus on what the file actually contains and its likely "
        f"purpose.{truncation_note}\n\n"
        f"File name: {Path(file_path).name}\n\n"
        f"Content:\n{content_to_send}"
    )

    system_instruction = (
        "You are a file summarization assistant. Write concise, "
        "factual summaries. Do not include phrases like 'this file "
        "contains' repeatedly — just describe the actual content "
        "directly and naturally."
    )

    try:
        summary = llm_engine.ask_llm(prompt, system_instruction=system_instruction)
        return summary
    except llm_engine.LLMConnectionError as error:
        raise SummarizerError(f"Failed to generate summary: {error}")


def summarize_folder(folder_path: str, recursive: bool = False) -> dict:

    try:
        all_files = file_scanner.list_files_in_folder(folder_path, recursive=recursive)
    except file_scanner.FileScannerError as error:
        raise SummarizerError(f"Could not scan folder: {error}")

    if not all_files:
        raise SummarizerError(f"'{folder_path}' contains no files to summarize.")

    file_summaries = {}
    files_skipped = 0

    files_to_process = all_files[:MAX_FILES_TO_SUMMARIZE_PER_FOLDER]

    for file_path in files_to_process:
        try:
            summary = summarize_file(str(file_path))
            file_summaries[file_path.name] = summary
        except SummarizerError:
         
            files_skipped += 1
            continue

    if not file_summaries:
        raise SummarizerError(
            f"None of the {len(all_files)} file(s) in '{folder_path}' "
            f"could be summarized. This usually means the folder "
            f"contains only non-text files (images, PDFs, etc), which "
            f"aren't supported yet."
        )


    combined_summaries_text = "\n".join(
        f"- {file_name}: {summary}"
        for file_name, summary in file_summaries.items()
    )

    folder_name = Path(folder_path).name

    prompt = (
        f"Here are summaries of individual files inside a folder "
        f"named '{folder_name}'. Based on these, write a short "
        f"2-3 sentence overview describing what this folder as a "
        f"whole appears to contain and its likely purpose.\n\n"
        f"{combined_summaries_text}"
    )

    system_instruction = (
        "You are a folder summarization assistant. Write a concise, "
        "high-level overview based on the individual file summaries "
        "provided. Do not list every file individually — synthesize "
        "a general picture."
    )

    try:
        folder_summary = llm_engine.ask_llm(prompt, system_instruction=system_instruction)
    except llm_engine.LLMConnectionError as error:
        raise SummarizerError(f"Failed to generate folder overview: {error}")

    return {
        "folder_summary": folder_summary,
        "file_summaries": file_summaries,
        "files_skipped": files_skipped + (len(all_files) - len(files_to_process)),
        "total_files_found": len(all_files),
    }



if __name__ == "__main__":
    print("summarizer.py self-test")
    print("-" * 50)

    print("Checking Ollama connection before running tests...")
    if not llm_engine.is_ollama_available():
        print("FAILED — Ollama is not reachable. Start Ollama and try again.")
        exit(1)
    print("OK — Ollama is reachable.")

    print("-" * 50)
    print(f"Scanning for a text file in: {config.DOWNLOADS_DIR}")

    try:
        all_files = file_scanner.list_files_in_folder(
            str(config.DOWNLOADS_DIR), recursive=False
        )
    except file_scanner.FileScannerError as error:
        print(f"FAILED — {error}")
        exit(1)

    text_files = [
        f for f in all_files
        if file_scanner.classify_file_type(str(f)) == "text"
    ]

    if not text_files:
        print("No plain text files found directly in Downloads, so the")
        print("single-file summary test will be skipped. This is not a")
        print("failure — just nothing suitable to test with right now.")
    else:
        sample_file = text_files[0]
        print(f"Testing summarize_file() on: {sample_file.name}")
        try:
            summary = summarize_file(str(sample_file))
            print(f"Summary: {summary}")
            print("OK — single file summary generated successfully.")
        except SummarizerError as error:
            print(f"FAILED — {error}")
            exit(1)

    print("-" * 50)
    print(f"Testing summarize_folder() on: {config.DOWNLOADS_DIR}")
    try:
        result = summarize_folder(str(config.DOWNLOADS_DIR), recursive=False)
        print(f"Total files found: {result['total_files_found']}")
        print(f"Files skipped: {result['files_skipped']}")
        print(f"Files individually summarized: {len(result['file_summaries'])}")
        print()
        print("Individual summaries:")
        for file_name, summary in result["file_summaries"].items():
            print(f"  - {file_name}: {summary}")
        print()
        print(f"Combined folder summary:\n{result['folder_summary']}")
    except SummarizerError as error:
        print(f"FAILED — {error}")
        exit(1)

    print("-" * 50)
    print("summarizer.py self-test complete.")