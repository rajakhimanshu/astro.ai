import pypdf
import os

pdf_path = "Brihat Parāśara Horā Śhāstra By R. Santhanam.pdf"
output_path = "knowledge/bphs.txt"

if os.path.exists(pdf_path):
    print(f"-> Extracting text from {pdf_path}...")
    reader = pypdf.PdfReader(pdf_path)
    with open(output_path, "w", encoding="utf-8") as f:
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                f.write(f"\n--- Page {i+1} ---\n")
                f.write(text)
            if (i+1) % 50 == 0:
                print(f"   Processed {i+1} pages...")
    print(f"✅ Extracted text to {output_path}")
else:
    print(f"❌ PDF not found: {pdf_path}")
