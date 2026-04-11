import os
import pdfplumber
import pytesseract
from pdf2image import convert_from_path
from core.knowledge_base import add_knowledge_chunk

# Configuration
STUDY_DATA_DIR = "study data"
KNOWLEDGE_DIR = "knowledge"
TESSERACT_PATH = r'C:\Program Files\Tesseract-OCR\tesseract.exe' # Default path, update if different

if os.path.exists(TESSERACT_PATH):
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

def extract_text_simple(pdf_path):
    """Extracts text from searchable PDFs."""
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            content = page.extract_text()
            if content:
                text += content + "\n"
    return text

def extract_text_ocr(pdf_path, lang='eng+hin'):
    """Extracts text from scanned PDFs using OCR (Supports Hindi)."""
    text = ""
    print(f"   -> Running OCR on {os.path.basename(pdf_path)} (this may take time)...")
    try:
        images = convert_from_path(pdf_path)
        for i, image in enumerate(images):
            page_text = pytesseract.image_to_string(image, lang=lang)
            text += f"\n--- Page {i+1} ---\n{page_text}"
    except Exception as e:
        print(f"   ❌ OCR Error: {e}")
    return text

def process_file(file_name):
    file_path = os.path.join(STUDY_DATA_DIR, file_name)
    print(f"Processing: {file_name}...")
    
    content = ""
    if file_name.endswith(".txt"):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    elif file_name.endswith(".pdf"):
        # Try simple extraction first
        content = extract_text_simple(file_path)
        # If very little text is extracted, it's likely a scanned PDF
        if len(content.strip()) < 100:
            content = extract_text_ocr(file_path)
    
    if content:
        # Save a copy to knowledge folder
        txt_name = os.path.splitext(file_name)[0] + ".txt"
        with open(os.path.join(KNOWLEDGE_DIR, txt_name), 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Add to ChromaDB in chunks
        print(f"   -> Chunking and adding to Vector DB...")
        # Simple chunking by paragraph/page for now
        chunks = [c.strip() for c in content.split('\n\n') if len(c.strip()) > 50]
        for chunk in chunks:
            add_knowledge_chunk(chunk, source=file_name)
        print(f"   ✅ Successfully indexed {len(chunks)} chunks.")

def main():
    if not os.path.exists(KNOWLEDGE_DIR):
        os.makedirs(KNOWLEDGE_DIR)
        
    files = [f for f in os.listdir(STUDY_DATA_DIR) if f.endswith(('.pdf', '.txt'))]
    print(f"Found {len(files)} files to process.")
    
    for f in files:
        try:
            process_file(f)
        except Exception as e:
            print(f"❌ Failed to process {f}: {e}")

if __name__ == "__main__":
    main()
