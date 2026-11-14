import os
import json
import psycopg2

# Connect using environment variables (defaults to local or Vultr connection string)
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_NAME = os.getenv("POSTGRES_DB", "ap_agent")
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "postgres")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")

def seed_database():
    print(f"Connecting to PostgreSQL at {DB_HOST}:{DB_PORT}...")
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            port=DB_PORT
        )
        cur = conn.cursor()
        
        # 1. Create tables for ground truth and invoices
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ground_truth (
                invoice_id VARCHAR(50) PRIMARY KEY,
                vendor_name VARCHAR(100),
                has_issue BOOLEAN,
                issue_type VARCHAR(50),
                total_amount NUMERIC(10, 2),
                payload JSONB
            );
        """)
        
        # 2. Load labels.json generated earlier
        labels_path = "data/corpus/labels.json"
        if not os.path.exists(labels_path):
            print(f"Error: {labels_path} not found. Run generate_full_corpus.py first.")
            return

        with open(labels_path, "r") as f:
            labels = json.load(f)
            
        # 3. Insert each record into PostgreSQL
        count = 0
        for inv_id, data in labels.items():
            cur.execute("""
                INSERT INTO ground_truth (invoice_id, vendor_name, has_issue, issue_type, total_amount, payload)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (invoice_id) DO UPDATE 
                SET vendor_name = EXCLUDED.vendor_name,
                    has_issue = EXCLUDED.has_issue,
                    issue_type = EXCLUDED.issue_type,
                    total_amount = EXCLUDED.total_amount,
                    payload = EXCLUDED.payload;
            """, (
                inv_id,
                data['vendor_name'],
                data['has_issue'],
                data['issue_type'],
                data['total_amount'],
                json.dumps(data)
            ))
            count += 1
            
        conn.commit()
        cur.close()
        conn.close()
        print(f"Successfully seeded {count} invoice records and ground truth data into PostgreSQL!")

    except Exception as e:
        print(f"Database connection note: {e}")
        print("This is normal if PostgreSQL isn't running yet. Keep this script ready for when Vultr Managed Postgres is live!")

if __name__ == "__main__":
    seed_database()
