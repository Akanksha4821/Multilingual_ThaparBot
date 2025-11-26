#!/usr/bin/env python3
"""
ThaparGpt - Clean Multilingual RAG + Multimodal Assistant
----------------------------------------------------------
Ready for UI integration. Supports text, images, and PDFs.
"""

import os
import logging
from typing import List, Optional, Union
from dotenv import load_dotenv

import chromadb
from sentence_transformers import SentenceTransformer
from google import genai
from google.genai.types import Part
from deep_translator import GoogleTranslator

load_dotenv()

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger("ThaparGpt")

# Language Detection Setup
USE_LINGUA = False
USE_LANGDETECT = False
try:
    from lingua import LanguageDetectorBuilder
    detector = LanguageDetectorBuilder.from_all_languages().build()
    USE_LINGUA = True
except:
    try:
        from langdetect import DetectorFactory, detect
        DetectorFactory.seed = 0
        USE_LANGDETECT = True
    except:
        pass


def detect_language(text: str):
    """
    Detect language with English as strong default.
    Only switch from English if VERY confident it's another language.
    """
    # If text is short or looks mostly English, default to English
    # This prevents false detection on words like "srilanka", "thapar", etc.
    
    text_lower = text.lower().strip()
    
    # Quick check: if text uses Latin alphabet mostly and has common English patterns
    english_indicators = ['what', 'how', 'why', 'when', 'where', 'who', 'is', 'are', 
                          'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'of',
                          'can', 'could', 'would', 'should', 'will', 'do', 'does',
                          'tell', 'explain', 'describe', 'give', 'show', 'help',
                          'please', 'thank', 'hello', 'hi', 'hey']
    
    # If any common English word is present, likely English
    words = text_lower.split()
    if any(word in english_indicators for word in words):
        return "en", "English"
    
    # For short texts (< 5 words), default to English to avoid false detection
    if len(words) < 5:
        # Check if it's clearly non-Latin script (Hindi, Chinese, Arabic, etc.)
        latin_chars = sum(1 for c in text if c.isalpha() and ord(c) < 128)
        total_alpha = sum(1 for c in text if c.isalpha())
        if total_alpha > 0 and latin_chars / total_alpha > 0.7:
            return "en", "English"
    
    # Now try language detection for non-English text
    if USE_LINGUA:
        try:
            lang = detector.detect_language_of(text)
            if lang:
                code = lang.iso_code_639_1.name.lower()
                # Double-check: if detected as something obscure, default to English
                common_langs = ['en', 'hi', 'pa', 'es', 'fr', 'de', 'zh', 'ar', 'bn', 'ta', 'te', 'mr', 'gu', 'kn', 'ml']
                if code not in common_langs:
                    return "en", "English"
                return code, lang.name.title()
        except:
            pass
    
    if USE_LANGDETECT:
        try:
            iso = detect(text)
            # Same check for langdetect
            common_langs = ['en', 'hi', 'pa', 'es', 'fr', 'de', 'zh', 'ar', 'bn', 'ta', 'te', 'mr', 'gu', 'kn', 'ml']
            if iso not in common_langs:
                return "en", "English"
            return iso, iso.upper()
        except:
            pass
    
    return "en", "English"


class EmbeddingModel:
    def __init__(self, model_name="intfloat/e5-small-v2"):
        self.model = SentenceTransformer(model_name)

    def encode(self, text):
        if isinstance(text, str):
            text = [text]
        vecs = self.model.encode(text, convert_to_numpy=True)
        return [v.tolist() for v in vecs][0] if len(text) == 1 else [v.tolist() for v in vecs]


class VectorDB:
    def __init__(self, path="./chroma_db", collection_name="structured_data"):
        self.client = chromadb.PersistentClient(path=path)
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        self.embedder = EmbeddingModel()

    def query(self, text, top_k=3):
        emb = self.embedder.encode(text)
        try:
            res = self.collection.query(query_embeddings=[emb], n_results=top_k, include=["documents"])
            docs = res.get("documents")
            return docs[0] if docs and docs[0] else []
        except:
            return []


class GeminiLLM:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY missing")
        self.client = genai.Client(api_key=api_key)
        self.model_name = "gemini-2.0-flash"

    def generate(self, prompt: str, parts: Optional[List[Part]] = None) -> str:
        contents = []
        if parts:
            contents.extend(parts)
        contents.append(prompt)
        result = self.client.models.generate_content(model=self.model_name, contents=contents)
        return result.text


class ThaparAssistant:
    
    THAPAR_KEYWORDS = [
        "thapar", "tiet", "patiala", "hostel", "mess", "warden",
        "pg", "wifi", "cafeteria", "fee", "academic", "library",
        "lhc", "placement", "cgpa", "semester", "campus"
    ]

    def __init__(self, db: VectorDB, llm: GeminiLLM):
        self.db = db
        self.llm = llm

    def is_thapar_query(self, query: str) -> bool:
        q = query.lower()
        return any(k in q for k in self.THAPAR_KEYWORDS)

    def get_datetime(self):
        from datetime import datetime
        import pytz
        now = datetime.now(pytz.timezone("Asia/Kolkata"))
        return now.strftime("%A, %d %B %Y"), now.strftime("%I:%M %p")

    def build_prompt(self, query: str, contexts: List[str], lang: str, iso: str, has_media: bool) -> str:
        date_str, time_str = self.get_datetime()
        is_thapar = self.is_thapar_query(query)

        prompt = f"""You are a helpful multilingual AI assistant.

Current date: {date_str} | Time: {time_str} IST

INSTRUCTIONS:
1. {"Analyze the provided image/document carefully." if has_media else ""}
2. {"Use the RAG context below to answer Thapar-related questions." if is_thapar and contexts else "Answer using your general knowledge."}
3. Respond in: {lang} ({iso})
4. Be concise and helpful.
"""
        if is_thapar and contexts:
            prompt += "\n--- THAPAR CONTEXT ---\n"
            for i, c in enumerate(contexts[:3]):
                prompt += f"[{i+1}] {c}\n"
            prompt += "--- END CONTEXT ---\n"

        prompt += f"\nUser: {query}\n\nAssistant:"
        return prompt

    def ask(
        self,
        query: str = "",
        image_bytes: bytes = None,
        image_mime: str = "image/jpeg",
        pdf_bytes: bytes = None,
        file_bytes: bytes = None,
        file_mime: str = None
    ) -> str:
        """
        Main method for UI integration.
        
        Args:
            query: User's text question (optional if file provided)
            image_bytes: Raw image bytes from upload
            image_mime: MIME type of image (image/jpeg, image/png, etc.)
            pdf_bytes: Raw PDF bytes from upload
            file_bytes: Generic file bytes (auto-detect type via file_mime)
            file_mime: MIME type for generic file
        
        Returns:
            Assistant's response as string
        """
        
        # Build media parts
        parts = []
        
        if image_bytes:
            parts.append(Part.from_bytes(data=image_bytes, mime_type=image_mime))
        
        if pdf_bytes:
            parts.append(Part.from_bytes(data=pdf_bytes, mime_type="application/pdf"))
        
        if file_bytes and file_mime:
            parts.append(Part.from_bytes(data=file_bytes, mime_type=file_mime))
        
        # Default query if only media provided
        if not query and parts:
            query = "Analyze this and describe what you see."
        
        if not query:
            return "Please provide a question or upload a file."
        
        # Detect language
        iso, lang = detect_language(query)
        
        # Get RAG context if Thapar-related
        contexts = self.db.query(query, top_k=3) if self.is_thapar_query(query) else []
        
        # Build prompt
        prompt = self.build_prompt(query, contexts, lang, iso, has_media=bool(parts))
        
        # Generate response
        response = self.llm.generate(prompt, parts=parts if parts else None)
        
        # Translate if needed
        if iso != "en":
            try:
                resp_iso, _ = detect_language(response)
                if resp_iso == "en":
                    response = GoogleTranslator(source="auto", target=iso).translate(response)
            except:
                pass
        
        return response


# =============================================================================
# READY-TO-USE FUNCTIONS FOR YOUR UI
# =============================================================================

# Initialize once when your app starts
_db = None
_llm = None
_assistant = None

def init_assistant():
    """Call this once when your app/server starts."""
    global _db, _llm, _assistant
    _db = VectorDB()
    _llm = GeminiLLM()
    _assistant = ThaparAssistant(_db, _llm)
    return _assistant

def get_assistant():
    """Get the assistant instance."""
    global _assistant
    if _assistant is None:
        init_assistant()
    return _assistant


# Simple functions your UI can call directly:

def chat(message: str) -> str:
    """Simple text chat."""
    return get_assistant().ask(query=message)


def chat_with_image(image_bytes: bytes, question: str = "", mime_type: str = "image/jpeg") -> str:
    """Chat with an uploaded image."""
    return get_assistant().ask(query=question, image_bytes=image_bytes, image_mime=mime_type)


def chat_with_pdf(pdf_bytes: bytes, question: str = "") -> str:
    """Chat with an uploaded PDF."""
    return get_assistant().ask(query=question, pdf_bytes=pdf_bytes)


def chat_with_file(file_bytes: bytes, mime_type: str, question: str = "") -> str:
    """Chat with any uploaded file."""
    return get_assistant().ask(query=question, file_bytes=file_bytes, file_mime=mime_type)


# =============================================================================
# CLI FOR TESTING (Remove this section in production)
# =============================================================================

def test_cli():
    """Simple CLI for testing. Your UI will replace this."""
    print("\n🎓 ThaparGPT Ready!\n")
    print("Commands:")
    print("  Type any question")
    print("  img <local_path> [question]  - Test with local image")
    print("  pdf <local_path> [question]  - Test with local PDF")
    print("  exit - Quit\n")
    
    init_assistant()
    
    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        
        if not user_input:
            continue
        if user_input.lower() == "exit":
            break
        
        # Test image
        if user_input.lower().startswith("img "):
            parts = user_input[4:].split(" ", 1)
            path = parts[0]
            question = parts[1] if len(parts) > 1 else ""
            
            if os.path.exists(path):
                with open(path, "rb") as f:
                    img_bytes = f.read()
                mime = "image/png" if path.lower().endswith(".png") else "image/jpeg"
                response = chat_with_image(img_bytes, question, mime)
                print(f"\nBot: {response}\n")
            else:
                print(f"File not found: {path}\n")
            continue
        
        # Test PDF
        if user_input.lower().startswith("pdf "):
            parts = user_input[4:].split(" ", 1)
            path = parts[0]
            question = parts[1] if len(parts) > 1 else ""
            
            if os.path.exists(path):
                with open(path, "rb") as f:
                    pdf_bytes = f.read()
                response = chat_with_pdf(pdf_bytes, question)
                print(f"\nBot: {response}\n")
            else:
                print(f"File not found: {path}\n")
            continue
        
        # Normal text
        response = chat(user_input)
        print(f"\nBot: {response}\n")


if __name__ == "__main__":
    test_cli()