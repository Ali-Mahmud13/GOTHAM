"""
Populate patient_latest_assessments directly via SQL.

Since triggers are active, we just need to trigger UPDATE on existing assessment records.
"""

import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

def populate_via_sql():
    """Populate by triggering assessment updates."""
    database_url = os.getenv("DATABASE_URL")
    
    print("Connecting to database...")
    conn = psycopg2.connect(database_url)
    cursor = conn.cursor()
    
    try:
        # For each assessment table, run a dummy UPDATE to trigger the function
        # This will cause triggers to fire and populate the materialized table
        
        print("\nTriggering GDM assessment updates...")
        cursor.execute("""
            UPDATE gdm_assessments 
            SET glucose_level = glucose_level 
            WHERE glucose_level IS NOT NULL
        """)
        gdm_count = cursor.rowcount
        print(f"  Updated {gdm_count} GDM assessment records")
        
        print("\nTriggering Anemia assessment updates...")
        cursor.execute("""
            UPDATE anemia_assessments
            SET wbc = wbc
            WHERE wbc IS NOT NULL
        """)
        anemia_count = cursor.rowcount
        print(f"  Updated {anemia_count} Anemia assessment records")
        
        print("\nTriggering Fetal Health assessment updates...")
        cursor.execute("""
            UPDATE fetal_health_assessments
            SET baseline_value = baseline_value  
            WHERE baseline_value IS NOT NULL
        """)
        fetal_count = cursor.rowcount
        print(f"  Updated {fetal_count} Fetal Health assessment records")
        
        conn.commit()
        
        # Check results
        print("\nVerifying population...")
        cursor.execute("SELECT COUNT(*) FROM patient_latest_assessments")
        count = cursor.fetchone()[0]
        print(f"✓ patient_latest_assessments now has {count} records")
        
        # Show sample
        cursor.execute("""
            SELECT p.patient_identifier,  p.name, pla.last_updated
            FROM patient_latest_assessments pla
            JOIN patients p ON p.id = pla.patient_id
            LIMIT 5
        """)
        
        print("\nSample records:")
        for row in cursor.fetchall():
            print(f"  {row[0]} - {row[1]} (updated: {row[2]})")
        
        print("\n✓ Migration complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
        import traceback
        traceback.print_exc()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    populate_via_sql()
