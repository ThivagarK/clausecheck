import psycopg2

conn = psycopg2.connect("dbname=ap_agent user=postgres password=postgres host=localhost port=5432")
cur = conn.cursor()

# Enable pgvector extension
cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")

# Create chunks table
cur.execute("""
CREATE TABLE IF NOT EXISTS chunks (
    id SERIAL PRIMARY KEY,
    vendor_id VARCHAR(50),
    doc_type VARCHAR(50),
    doc_name VARCHAR(255),
    header_path TEXT,
    effective_date DATE,
    supersedes_clause VARCHAR(100),
    content TEXT,
    embedding vector(384)
);
""")

conn.commit()
cur.close()
conn.close()
print("Successfully created 'chunks' table and enabled pgvector extension!")
