import psycopg2
from sentence_transformers import SentenceTransformer

class APSearchEngine:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.conn = psycopg2.connect("dbname=ap_agent user=postgres password=postgres host=localhost port=5432")

    def search(self, query_text, vendor_id=None, doc_type=None, top_k=3):
        query_embedding = self.model.encode(query_text).tolist()
        
        cur = self.conn.cursor()
        
        sql = """
            SELECT vendor_id, doc_type, doc_name, header_path, effective_date, supersedes_clause, content,
                   (embedding <=> %s::vector) as distance
            FROM chunks
            WHERE 1=1
        """
        params = [str(query_embedding)]
        
        if vendor_id:
            sql += " AND vendor_id = %s"
            params.append(vendor_id)
            
        if doc_type:
            sql += " AND doc_type = %s"
            params.append(doc_type)
            
        sql += " ORDER BY embedding <=> %s::vector LIMIT %s;"
        params.extend([str(query_embedding), top_k * 2]) # Fetch extra to handle supersession filtering
        
        cur.execute(sql, params)
        results = cur.fetchall()
        cur.close()
        
        raw_hits = []
        for r in results:
            raw_hits.append({
                "vendor_id": r[0],
                "doc_type": r[1],
                "doc_name": r[2],
                "header_path": r[3],
                "effective_date": str(r[4]) if r[4] else None,
                "supersedes_clause": r[5],
                "content": r[6],
                "similarity_score": 1.0 - float(r[7])
            })
            
        # Supersession Logic: If an amendment supersedes an older clause, filter out the old one or prioritize the latest effective date
        superseded_clauses = set(h["supersedes_clause"] for h in raw_hits if h["supersedes_clause"])
        
        filtered_hits = []
        for h in raw_hits:
            # Check if this chunk's clause header matches a superseded clause tag
            is_superseded = False
            for sc in superseded_clauses:
                if sc and sc in h["header_path"]:
                    is_superseded = True
                    break
            if not is_superseded:
                filtered_hits.append(h)
                
        return filtered_hits[:top_k]

if __name__ == "__main__":
    engine = APSearchEngine()
    query = "What is the standard consulting rate?"
    print(f"\nQuery: '{query}'")
    hits = engine.search(query, top_k=2)
    for h in hits:
        print(f"[{h['doc_name']}] ({h['header_path']}) | Effective: {h['effective_date']} | Score: {h['similarity_score']:.4f}")
        print(f"Content: {h['content'][:150]}...\n")
