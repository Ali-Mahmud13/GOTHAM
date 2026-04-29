"""Show database connection info and table list."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlmodel import Session, text
from app.db.session import engine
from app.core.config import DATABASE_URL

def main():
    """Display database info."""
    print("\n" + "="*60)
    print("DATABASE CONNECTION INFO")
    print("="*60)
    
    # Show database URL (masked password)
    if DATABASE_URL:
        # Mask the password in the URL
        masked_url = DATABASE_URL
        if "@" in masked_url and ":" in masked_url:
            parts = masked_url.split("@")
            if len(parts) == 2:
                user_pass = parts[0].split("://")[1]
                if ":" in user_pass:
                    user, _ = user_pass.split(":", 1)
                    masked_url = masked_url.replace(user_pass, f"{user}:****")
        
        print(f"\nDatabase URL: {masked_url}")
        
        # Extract database name
        if "/" in masked_url:
            db_name = masked_url.split("/")[-1].split("?")[0]
            print(f"Database Name: {db_name}")
    
    print("\n" + "="*60)
    print("TABLES IN DATABASE")
    print("="*60)
    
    with Session(engine) as session:
        # Query to list all tables
        result = session.exec(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """))
        
        tables = result.all()
        
        if tables:
            print(f"\nFound {len(tables)} table(s):")
            for table in tables:
                print(f"  ✓ {table[0]}")
                
                # Count rows in each table
                try:
                    count_result = session.exec(text(f"SELECT COUNT(*) FROM {table[0]}"))
                    count = count_result.first()[0]
                    print(f"    → {count} rows")
                except Exception as e:
                    print(f"    → Error counting rows: {e}")
        else:
            print("\nNo tables found in 'public' schema!")
            print("Tables might be in a different schema.")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    main()
