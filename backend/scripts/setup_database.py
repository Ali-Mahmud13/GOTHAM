"""Setup script for initializing the database with patient and visit tables."""

import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.init_db import create_db_and_tables
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Initialize database tables."""
    logger.info("=" * 60)
    logger.info("Database Setup Script")
    logger.info("=" * 60)
    
    try:
        create_db_and_tables()
        logger.info("=" * 60)
        logger.info("✓ Database setup completed successfully!")
        logger.info("=" * 60)
        logger.info("\nNext steps:")
        logger.info("1. Run migration script: python scripts/migrate_csv_to_db.py")
        logger.info("2. Test the agent to verify it works with database")
    except Exception as e:
        logger.error(f"Failed to setup database: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
