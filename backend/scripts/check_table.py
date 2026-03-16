"""
Quick script to check if patient_latest_assessments table exists.
"""
import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

def check_table_exists():
    database_url = os.getenv("DATABASE_URL")
    
    try:
        conn = psycopg2.connect(database_url)
        cursor = cursor()
        
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'patient_latest_assessments'
            );
        """)
        
        exists = cursor.fetchone()[0]
        
        if exists:
            print("✓ Table 'patient_latest_assessments' exists")
            
            # Check row count
            cursor.execute("SELECT COUNT(*) FROM patient_latest_assessments")
            count = cursor.fetchone()[0]
            print(f"  Rows: {count}")
        else:
            print("✗ Table 'patient_latest_assessments' does not exist")
            print("\nThe table will be auto-created when the backend restarts")
            print("Or you can create it manually by restarting uvicorn")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_table_exists()
