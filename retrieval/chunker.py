
import os
import re
from pypdf import PdfReader

def extract_text_from_pdf(pdf_path):
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text

def chunk_contract(file_path, vendor_id, doc_name):
    text = extract_text_from_pdf(file_path)
    
    # Split by lines starting with or containing [CLAUSE-...], [AMENDMENT-], etc.
    # We use a positive lookahead on newline followed by brackets
    raw_chunks = re.split(r'\n(?=\[?(?:CLAUSE|AMENDMENT|SECTION)-[0-9A-Z\.]+\]?)', text, flags=re.IGNORECASE)
    
    chunks = []
    for part in raw_chunks:
        if not part.strip():
            continue
            
        lines = part.strip().split('\n')
        header = lines[0] if len(lines) > 0 else "General"
        
        # Extract effective date if present in text
        date_match = re.search(r'Effective Date:\s*([0-9]{4}-[0-9]{2}-[0-9]{2})', part, re.IGNORECASE)
        effective_date = date_match.group(1) if date_match else None
        
        # Extract supersession info if it's an amendment
        supersedes_match = re.search(r'supersedes\s+(?:clause|section)\s+([0-9A-Z\.]+)', part, re.IGNORECASE)
        supersedes_clause = supersedes_match.group(1) if supersedes_match else None
        
        chunks.append({
            "vendor_id": vendor_id,
            "doc_type": "contract" if "amendment" not in doc_name.lower() else "amendment",
            "doc_name": doc_name,
            "header_path": header,
            "effective_date": effective_date,
            "supersedes_clause": supersedes_clause,
            "content": part.strip()
        })
        
    return chunks

if __name__ == "__main__":
    sample_contract = "data/corpus/contracts/contract_acme_corp.pdf"
    if os.path.exists(sample_contract):
        chunks = chunk_contract(sample_contract, "V1", "contract_acme_corp.pdf")
        print(f"Successfully chunked sample contract into {len(chunks)} sections.")
        for i, c in enumerate(chunks[:3]):
            print(f"\n--- Chunk {i+1} Header: {c['header_path']} ---")
            print(c['content'][:150] + "...")
