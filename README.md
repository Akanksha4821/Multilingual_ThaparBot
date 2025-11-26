🌐 ThaparGPT — Multilingual RAG + Multimodal Assistant

ThaparGPT is a clean and efficient multilingual chatbot built using a RAG (Retrieval-Augmented Generation) pipeline. It supports English, Hindi, and Punjabi, and can process text, images, PDFs, and file uploads using Google Gemini Flash 2.0.
The system is designed for Thapar University PG students and answers campus-related queries using a structured vector database stored in ChromaDB.

✔️ Key Features

Multilingual detection with English-safe fallback

RAG-based contextual answers for Thapar-related queries

Multimodal support (Text + Images + PDFs + Files)

Gemini 2.0 Flash integration

Lightweight, clean architecture

Ready for React/HTML frontend integration

📌 Project Files & Their Use (as shown in your GitHub)
1. ThaparGpt.py (Main RAG Model – 367 LOC)

Contains the core intelligence of the project:

Language detection logic

Embedding generation using SentenceTransformer

ChromaDB vector search

RAG context retrieval

Gemini Flash 2.0 prompt building

Multimodal file/image/PDF handling

Auto-translation for multilingual responses

Exposes functions: chat(), chat_with_image(), chat_with_pdf(), chat_with_file()

This is the heart of the system.

2. app.py (Flask API Backend – 481 LOC)

Implements all REST API endpoints needed by your UI:

Text chat API

Image/PDF/File upload APIs

Admin login, view feedback, update RAG

CORS handling

Communication layer between UI ↔ ThaparGpt.py

This file makes the model usable through any frontend.

3. index.html (Frontend UI – 1044 LOC)

A complete web interface that allows users to:

Type queries

Upload images/PDFs/files

Display model responses

Serve as the main demo UI for the project

Only for presentation and user interaction.

4. convert_to_utf8.py (Data Encoding Cleaner – 29 LOC)

Converts every .txt file inside Structured_Data/ to UTF-8 using chardet.
Ensures data consistency before embedding.

5. create_structured_collection.py (ChromaDB Builder – 60 LOC)

Loads cleaned text files → generates embeddings → stores them into ChromaDB.
Automatically builds the vector database used by the RAG system.

6. DataPreProcessing.ipynb (~100 LOC)

Notebook used for dataset cleaning, formatting, and manual corrections before UTF-8 conversion and embedding.
