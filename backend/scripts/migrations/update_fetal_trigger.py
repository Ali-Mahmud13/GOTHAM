"""Update fetal trigger to include all CTG fields."""

import os
from dotenv import load_dotenv
import psycopg2
from pathlib import Path

load_dotenv()

def update_fetal_trigger():
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cursor = conn.cursor()
    
    sql_file = Path(__file__).parent / "update_fetal_trigger.sql"
    with open(sql_file, 'r') as f:
        sql = f.read()
    
    print("Updating fetal trigger to include all CTG fields...")
    
    try:
        cursor.execute(sql)
        conn.commit()
        print("✓ Fetal trigger updated successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
        import traceback
        traceback.print_exc()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    update_fetal_trigger()
