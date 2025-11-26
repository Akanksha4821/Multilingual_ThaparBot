🌐 ThaparGPT — Multilingual RAG + Multimodal Assistant

ThaparGPT is a clean and efficient multilingual chatbot built using a RAG (Retrieval-Augmented Generation) pipeline.
It supports English, Hindi, and Punjabi, and can process text, images, PDFs, and file uploads using Google Gemini Flash 2.0.
The system is designed for Thapar University PG students and answers campus-related queries using a structured vector database stored in ChromaDB.

✔️ Key Features

Multilingual detection with English-safe fallback

RAG-based contextual answers for Thapar-related queries

Multimodal support (Text + Images + PDFs + Files)

Gemini 2.0 Flash integration

Lightweight, clean architecture

Ready for React/HTML frontend integration

📌 Project Files & Their Use

1️⃣ ThaparGpt.py (Main RAG Model – 367 LOC)

Contains the core intelligence of the project:

Language detection logic

Embedding generation using SentenceTransformer

ChromaDB vector search

RAG context retrieval

Gemini Flash 2.0 prompt building

Multimodal file/image/PDF handling

Auto-translation for multilingual responses

Provides: chat(), chat_with_image(), chat_with_pdf(), chat_with_file()

This is the heart of the system.

2️⃣ app.py (Flask API Backend – 481 LOC)

Implements all REST API endpoints needed by the UI:

Text chat API

Image/PDF/File upload APIs

Admin login, view feedback, update RAG

CORS handling

Communication layer between UI ↔ ThaparGpt.py

This file makes the model usable through any frontend.

3️⃣ index.html (Frontend UI – 1044 LOC)

A complete web interface enabling:

Typing user queries

Uploading images/PDFs/files

Displaying model responses

Used only for demo and user interaction.

4️⃣ convert_to_utf8.py (Data Encoding Cleaner – 29 LOC)

Converts all .txt files in Structured_Data/ to UTF-8

Uses chardet to detect source encoding

Ensures consistent data before embedding

5️⃣ create_structured_collection.py (ChromaDB Builder – 60 LOC)

Reads cleaned text files

Generates embeddings using e5-small-v2

Stores vectors + metadata into ChromaDB

Automatically builds the vector database used by the RAG system

6️⃣ DataPreProcessing.ipynb (~100 LOC)

Notebook for data cleaning and formatting

Removes noise, normalizes text, and prepares structured data

Used before UTF-8 conversion and embedding
