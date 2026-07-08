import os
from pathlib import Path

APP_NAME = "AI-OS"
APP_VERSION = "0.1.0"

#file system paths
USER_HOME_DIR = Path.home()
DOWNLOADS_DIR = USER_HOME_DIR / "Downloads"
DOCUMENTS_DIR = USER_HOME_DIR / "Documents"
APP_DATA_DIR = Path(os.environ.get("LOCALAPPDATA", USER_HOME_DIR)) / APP_NAME
VECTOR_DB_DIR = APP_DATA_DIR / "vector_store"
LOGS_DIR = APP_DATA_DIR / "logs"



def ensure_app_directories_exist() -> None:
    #Ensure that the required application directories exist.
    try:
        APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
        VECTOR_DB_DIR.mkdir(parents=True, exist_ok=True)
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        #if any folder creation fails, raising a RuntimeError with a message 
        raise RuntimeError(
            f"AI-OS failed to create required application folders. "
            f"Check that you have write permission to {APP_DATA_DIR}. "
            f"Original error: {error}"
        )
    
#ollama
OLLAMA_MODEL_NAME = "phi3"
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_REQUEST_TIMEOUT_SECONDS = 69
OLLAMA_TEMPERATURE = 0.2

#embeddings and vector search settings
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
CHROMA_COLLECTION_NAME = "ai_os_file_index"

#file settings
SUPPORTED_TEXT_EXTENSIONS = {
    ".txt", ".md", ".csv", ".json", ".log",
    ".py", ".js", ".html", ".css",
}
SUPPORTED_DOCUMENT_EXTENSIONS = {
    ".pdf", ".docx",
}
IMAGE_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg",
}
VIDEO_EXTENSIONS = {
    ".mp4", ".mov", ".avi", ".mkv", ".wmv", ".flv",
}
MAX_READABLE_FILE_SIZE_BYTES = 10 * 1024 * 1024

#UI Theme settings
UI_BACKGROUND_COLOR = "#0D0D0D" 
UI_TEXT_COLOR = "#E0E0E0" 
UI_BORDER_COLOR = "#2A2A2A"
UI_ACCENT_COLOR = "#FFFFFF" 

UI_FONT_FAMILY = "JetBrains Mono, Consolas, monospace"
UI_FONT_SIZE_NORMAL = 11
UI_FONT_SIZE_SMALL = 9

#test
if __name__ == "__main__":
    print(f"{APP_NAME} v{APP_VERSION} — config.py self-test")
    print("-" * 50)

    print(f"User home directory:   {USER_HOME_DIR}")
    print(f"Downloads directory:   {DOWNLOADS_DIR}")
    print(f"Documents directory:   {DOCUMENTS_DIR}")
    print(f"App data directory:    {APP_DATA_DIR}")
    print(f"Vector DB directory:   {VECTOR_DB_DIR}")
    print(f"Logs directory:        {LOGS_DIR}")
    print("-" * 50)

    print("Creating application directories if missing...")
    ensure_app_directories_exist()

    for label, path in [
        ("App data", APP_DATA_DIR),
        ("Vector DB", VECTOR_DB_DIR),
        ("Logs", LOGS_DIR),
    ]:
        status = "OK — exists" if path.exists() else "FAILED — missing"
        print(f"{label} directory: {status} ({path})")

    print("-" * 50)
    print(f"Ollama model:          {OLLAMA_MODEL_NAME}")
    print(f"Ollama base URL:       {OLLAMA_BASE_URL}")
    print(f"Embedding model:       {EMBEDDING_MODEL_NAME}")
    print(f"Chroma collection:     {CHROMA_COLLECTION_NAME}")
    print("-" * 50)
    print("config.py self-test complete. If all directories say")
    print("'OK — exists' above, this file is working correctly.")
