import os
import glob
import psycopg2
from sentence_transformers import SentenceTransformer
from chunker import chunk_contract, extract_text_from_pdf

def ingest_corpus():
    print("Initializing embedding model (all-MiniLM-L6-v2)...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    conn = psycopg2.connect("dbname=ap_agent user=postgres password=postgres host=localhost port=5432")
    cur = conn.cursor()
    
    # Clear existing chunks to avoid duplication on re-runs
    cur.execute("TRUNCATE TABLE chunks RESTART IDENTITY;")
    conn.commit()
    
    # Find all PDFs in corpus
    pdf_files = glob.glob("data/corpus/**/*.pdf", recursive=True)
    print(f"Found {len(pdf_files)} PDF documents in corpus. Starting ingestion...")
    
    total_chunks = 0
    
    for file_path in pdf_files:
        filename = os.path.basename(file_path)
        rel_path = os.path.relpath(file_path, "data/corpus")
        
        # Determine doc_type and vendor_id from path/filename
        doc_type = "invoice"
        vendor_id = None
        
        if "contracts" in rel_path or "amendment" in filename.lower():
            doc_type = "contract" if "amendment" not in filename.lower() else "amendment"
            # Extract vendor id from filename e.g. contract_acme_corp.pdf -> V1 or match labels
            # Let's derive a clean vendor_id from filename
            parts = filename.replace(".pdf", "").split("_")
            if len(parts) > 1:
                vendor_id = parts[1].upper()
            else:
                vendor_id = "UNKNOWN"
        elif "policies" in rel_path:
            doc_type = "policy"
            vendor_id = "INTERNAL"
        elif "invoices" in rel_path:
            doc_type = "invoice"
            # Extract vendor from invoice or assign based on naming
            vendor_id = "V_INVOICE"
            
        # Process chunks depending on document type
        if doc_type in ["contract", "amendment"]:
            chunks = chunk_contract(file_path, vendor_id, filename)
        else:
            # For invoices and policies, treat paragraphs or pages as chunks
            text = extract_text_from_pdf(file_path)
            paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
            if not paragraphs:
                paragraphs = [text.strip()]
                
            chunks = []
            for idx, para in enumerate(paragraphs):
                chunks.append({
                    "vendor_id": vendor_id,
                    "doc_type": doc_type,
                    "doc_name": filename,
                    "header_path": f"{filename} - Part {idx+1}",
                    "effective_date": None,
                    "supersedes_clause": None,
                    "content": para
                })
        
        # Generate embeddings and insert into DB
        for chunk in chunks:
            content = chunk["content"]
            embedding = model.encode(content).tolist()
            
            cur.execute("""
                INSERT INTO chunks (vendor_id, doc_type, doc_name, header_path, effective_date, supersedes_clause, content, embedding)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
            """, (
                chunk["vendor_id"],
                chunk["doc_type"],
                chunk["doc_name"],
                chunk["header_path"],
                chunk["effective_date"],
                chunk["supersedes_clause"],
                chunk["content"],
                str(embedding) # pgvector accepts list as string or vector format
            ))
            total_chunks += 1
            
    conn.commit()
    cur.close()
    conn.close()
    print(f"Successfully ingested {total_chunks} total chunks into PostgreSQL!")

if __name__ == "__main__":
    ingest_corpus()
