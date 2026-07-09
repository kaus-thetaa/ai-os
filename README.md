# AI-OS

An offline AI layer over the Windows file system. Search, summarize, rename,
organize, and deduplicate files using natural language powered entirely by
a local LLM (Phi-3 Mini via Ollama). No cloud APIs, no data leaves your machine.

## Status: In Development

## Features (planned)
- [ ] Natural language file search
- [ ] Folder/document summarization
- [ ] Content-based intelligent file renaming
- [ ] Automatic Downloads folder organization
- [ ] Duplicate file detection
- [ ] Local searchable knowledge base (vector search over your documents)

## Tech Stack
- Python 3.11+
- Ollama (Phi-3 Mini) — local LLM inference
- PyQt6 — desktop UI
- sentence-transformers — offline embeddings
- ChromaDB — local vector database

## Why offline?
No API keys, no rate limits, no subscription, no data privacy concerns.
Everything runs on your machine.

## Setup
(instructions coming as the project develops)

## Architecture
(diagram/explanation coming once core modules are built)