# pdf_to_knowledge.py
import os
import sys
import chromadb
import ollama
import time

# PDF and OCR Libraries
try:
    import fitz  # pymupdf
    PDF_ENGINE = "pymupdf"
except ImportError:
    print("Please install pymupdf: pip install pymupdf")
    sys.exit(1)

try:
    import pytesseract
    from pdf2image import convert_from_path
    OCR_AVAILABLE = True
    # Default Tesseract path for Windows
    TESSERACT_PATH = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    if os.path.exists(TESSERACT_PATH):
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
except ImportError:
    OCR_AVAILABLE = False
    print("OCR libraries not found. Scanned PDFs will be skipped.")

# Setup ChromaDB
chroma_client = chromadb.PersistentClient(path="data/chroma_db")
knowledge_collection = chroma_client.get_or_create_collection("astro_knowledge")

def extract_text_ocr(pdf_path):
    """Fallback: Convert PDF to images and use OCR if text extraction fails"""
    if not OCR_AVAILABLE:
        return ""
    
    print(f"  -> Scanned PDF detected. Starting OCR (this may take time)...")
    try:
        images = convert_from_path(pdf_path)
        full_text = ""
        for i, image in enumerate(images):
            # OCR with English and Hindi support
            page_text = pytesseract.image_to_string(image, lang='eng+hin')
            full_text += f"\n--- OCR Page {i+1} ---\n{page_text}"
            if (i+1) % 5 == 0:
                print(f"     Processed {i+1}/{len(images)} pages...")
        return full_text
    except Exception as e:
        print(f"  OCR ERROR: {e}")
        return ""

def extract_text(file_path):
    """Extract text from PDF (with OCR fallback) or TXT"""
    if file_path.lower().endswith('.txt'):
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    # Try standard extraction first
    doc = fitz.open(file_path)
    full_text = ""
    for page_num, page in enumerate(doc):
        text = page.get_text()
        if text.strip():
            full_text += f"\n--- Page {page_num + 1} ---\n{text}"
    doc.close()
    
    # If we got almost nothing, try OCR
    if len(full_text.strip()) < 150 and OCR_AVAILABLE:
        full_text = extract_text_ocr(file_path)
        
    return full_text

def smart_chunk(text, chunk_size=1000, overlap=150):
    """Splits text into chunks, ensuring none exceed the AI's limit"""
    chunks = []
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    
    current_chunk = ""
    for para in paragraphs:
        # If a single paragraph is larger than our chunk size, break it forcefully
        if len(para) > chunk_size:
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = ""
            
            # Break massive paragraph into sub-chunks
            for i in range(0, len(para), chunk_size - overlap):
                chunks.append(para[i:i + chunk_size])
            continue

        if len(current_chunk) + len(para) < chunk_size:
            current_chunk += "\n\n" + para
        else:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = para if len(current_chunk) < overlap else current_chunk[-overlap:] + "\n\n" + para
            
    if current_chunk:
        chunks.append(current_chunk)
    return chunks

def embed_with_retry(text, retries=3):
    """Ollama embedding with retry logic for stability"""
    for i in range(retries):
        try:
            response = ollama.embeddings(model='nomic-embed-text', prompt=text)
            return response['embedding']
        except Exception as e:
            if i == retries - 1: raise e
            time.sleep(2)

def process_file(file_path, source_name):
    print(f"\n{'='*60}")
    print(f"PROCESSING: {source_name}")
    print(f"{'='*60}")
    
    text = extract_text(file_path)
    if not text.strip():
        print("  ❌ No content found.")
        return 0
    
    print(f"  ✓ Extracted {len(text)} characters.")
    chunks = smart_chunk(text)
    print(f"  ✓ Created {len(chunks)} chunks.")
    
    stored = 0
    for i, chunk in enumerate(chunks):
        if len(chunk.strip()) < 40: continue
        
        try:
            embedding = embed_with_retry(chunk)
            chunk_id = f"kb_{source_name}_{i}"
            
            knowledge_collection.upsert(
                ids=[chunk_id],
                embeddings=[embedding],
                documents=[chunk],
                metadatas=[{'source': source_name, 'chunk': i, 'type': 'classical_text'}]
            )
            stored += 1
            if (i+1) % 25 == 0: print(f"    Progress: {i+1}/{len(chunks)}...")
        except Exception as e:
            print(f"    Error on chunk {i}: {e}")
            
    print(f"  ✅ SUCCESS: Stored {stored} chunks from {source_name}")
    return stored

def run_sync():
    folders = ["raw_pdfs", "study data"]
    processed_sources = set()
    
    # Check what we already have
    try:
        existing = knowledge_collection.get()
        if existing['metadatas']:
            for m in existing['metadatas']:
                processed_sources.add(m.get('source'))
    except: pass

    total_new = 0
    for folder in folders:
        if not os.path.exists(folder): continue
        files = [f for f in os.listdir(folder) if f.lower().endswith(('.pdf', '.txt'))]
        
        for f in files:
            # We use filename as unique key. 
            # If you want to FORCE re-processing, delete it from ChromaDB first.
            if f in processed_sources:
                print(f"Skipping {f} (Already in knowledge base)")
                continue
            
            path = os.path.join(folder, f)
            total_new += process_file(path, f)

    print(f"\nDONE! Knowledge base size: {knowledge_collection.count()} chunks.")

if __name__ == "__main__":
    # Check Ollama connection
    try:
        ollama.list()
        run_sync()
    except Exception as e:
        print(f"Connection Error: {e}. Is Ollama running?")
