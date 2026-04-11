import os
import pdfplumber
import fitz  # PyMuPDF
import pytesseract
from pdf2image import convert_from_path
from langdetect import detect
from deep_translator import GoogleTranslator
from core.knowledge_base import add_knowledge_chunk

# --- CONFIGURATION ---
RAW_PDFS_DIR = "study data"  # Using your existing folder
KNOWLEDGE_DIR = "knowledge"
TESSERACT_PATH = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

if os.path.exists(TESSERACT_PATH):
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

translator = GoogleTranslator(source='hi', target='en')

def clean_text(text):
    """Basic cleaning of extracted text."""
    if not text: return ""
    # Remove excessive newlines and whitespace
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    return '\n'.join(lines)

def extract_with_pdfplumber(pdf_path):
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                content = page.extract_text()
                if content:
                    text += content + "\n"
    except Exception as e:
        print(f"      [pdfplumber error: {e}]")
    return text

def extract_with_fitz(pdf_path):
    text = ""
    try:
        doc = fitz.open(pdf_path)
        for page in doc:
            text += page.get_text()
    except Exception as e:
        print(f"      [fitz error: {e}]")
    return text

def extract_with_ocr(pdf_path):
    print(f"    -> Scanned PDF detected. Starting OCR (Hindi + English)...")
    text = ""
    try:
        images = convert_from_path(pdf_path)
        for i, image in enumerate(images):
            # OCR with both Hindi and English
            page_text = pytesseract.image_to_string(image, lang='hin+eng')
            text += f"\n{page_text}"
            if (i+1) % 10 == 0: print(f"       Processed {i+1} pages...")
    except Exception as e:
        print(f"      [OCR error: {e}]")
    return text

def process_hindi_text(text):
    """Detects Hindi and translates chunks to English."""
    try:
        if not text.strip(): return ""
        # Check if text is primarily Hindi
        # We check a sample to avoid issues with mixed text
        sample = text[:500]
        if detect(sample) == 'hi':
            print("    -> Hindi detected. Translating to English...")
            # GoogleTranslator has a character limit per request (usually 5000)
            chunks = [text[i:i+4500] for i in range(0, len(text), 4500)]
            translated_chunks = []
            for chunk in chunks:
                translated_chunks.append(translator.translate(chunk))
            return '\n'.join(translated_chunks)
    except Exception as e:
        print(f"      [Translation/Detection error: {e}]")
    return text

def process_pdf(file_name):
    pdf_path = os.path.join(RAW_PDFS_DIR, file_name)
    print(f"\nProcessing: {file_name}")
    
    # 1. Try smart extraction first
    text = extract_with_pdfplumber(pdf_path)
    
    # 2. If pdfplumber fails or gets very little, try Fitz
    if len(text.strip()) < 100:
        text = extract_with_fitz(pdf_path)
        
    # 3. If still very little, it's definitely a scanned image
    if len(text.strip()) < 100:
        text = extract_with_ocr(pdf_path)
    
    if not text.strip():
        print(f"    ❌ Could not extract any text from {file_name}")
        return

    # 4. Clean and Translate if needed
    text = clean_text(text)
    final_text = process_hindi_text(text)
    
    # 5. Save to Knowledge Folder
    txt_name = os.path.splitext(file_name)[0] + ".txt"
    output_path = os.path.join(KNOWLEDGE_DIR, txt_name)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(final_text)
    print(f"    ✅ Text saved to {output_path}")

    # 6. Index into ChromaDB
    print(f"    -> Indexing into Knowledge Base...")
    chunks = [c.strip() for c in final_text.split('\n\n') if len(c.strip()) > 100]
    for chunk in chunks:
        add_knowledge_chunk(chunk, source=file_name)
    print(f"    ✅ Indexed {len(chunks)} chunks.")

def main():
    if not os.path.exists(KNOWLEDGE_DIR): os.makedirs(KNOWLEDGE_DIR)
    
    files = [f for f in os.listdir(RAW_PDFS_DIR) if f.lower().endswith('.pdf')]
    print(f"Found {len(files)} PDFs in {RAW_PDFS_DIR}")
    
    for f in files:
        process_pdf(f)

if __name__ == "__main__":
    main()
