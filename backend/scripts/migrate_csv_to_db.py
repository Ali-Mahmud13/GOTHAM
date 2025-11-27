"""Data migration script to move CSV data to database."""

import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import logging
from datetime import datetime
from sqlmodel import Session
from app.db.session import engine
from app.models import Patient, Visit
from app.db.init_db import create_db_and_tables

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate_csv_to_database(csv_path: str | Path):
    """
    Migrate patient data from CSV file to database.
    
    This script:
    1. Reads the CSV file
    2. Creates Patient records with static features
    3. Creates Visit records with dynamic measurements
    
    Args:
        csv_path: Path to the CSV file containing patient data
    """
    logger.info(f"Starting migration from {csv_path}")
    
    # Ensure tables exist
    create_db_and_tables()
    
    # Read CSV
    df = pd.read_csv(csv_path)
    logger.info(f"Loaded {len(df)} rows from CSV")
    
    # Column mapping: CSV column name -> Database field name
    # Static features (patient-level)
    static_column_map = {
        'Family History': 'family_history',
        'PCOS': 'pcos',
        'unexplained prenatal loss': 'unexplained_prenatal_loss',
        'Large Child or Birth Default': 'large_child_or_birth_default',
        'Prediabetes': 'prediabetes'
    }
    
    # Dynamic features (visit-level)
    dynamic_column_map = {
        'Age': 'age',
        'BMI': 'bmi',
        'Sys BP': 'sys_bp',
        'Dia BP': 'dia_bp',
        'HDL': 'hdl',
        'Hemoglobin': 'hemoglobin',
        'OGTT': 'ogtt',
        'No of Pregnancy': 'no_of_pregnancy',
        'Gestation in previous Pregnancy': 'gestation_in_previous_pregnancy',
        'Sedentary Lifestyle': 'sedentary_lifestyle'
    }
    
    with Session(engine) as session:
        patients_created = 0
        visits_created = 0
        
        for idx, row in df.iterrows():
            patient_id = str(row['Patient_ID'])
            
            # Check if patient already exists
            existing_patient = session.query(Patient).filter(
                Patient.patient_identifier == patient_id
            ).first()
            
            if not existing_patient:
                # Create patient with static features
                patient_data = {
                    'patient_identifier': patient_id
                }
                
                for csv_col, db_field in static_column_map.items():
                    if csv_col in row:
                        value = row[csv_col]
                        if pd.notna(value):
                            # Convert to boolean if needed
                            if isinstance(value, (int, float)):
                                patient_data[db_field] = bool(value)
                            else:
                                patient_data[db_field] = value
                
                patient = Patient(**patient_data)
                session.add(patient)
                session.flush()  # Get the patient ID
                patients_created += 1
                logger.info(f"Created patient: {patient_id}")
            else:
                patient = existing_patient
                logger.info(f"Patient {patient_id} already exists, adding visit")
            
            # Create visit with dynamic features
            visit_data = {
                'patient_id': patient.id,
                'visit_date': datetime.utcnow(),  # Default to current time
                'visit_type': 'imported_from_csv'
            }
            
            for csv_col, db_field in dynamic_column_map.items():
                if csv_col in row:
                    value = row[csv_col]
                    if pd.notna(value):
                        # Convert to appropriate type
                        if db_field == 'sedentary_lifestyle':
                            visit_data[db_field] = bool(value) if isinstance(value, (int, float)) else value
                        elif db_field in ['age', 'no_of_pregnancy', 'gestation_in_previous_pregnancy', 'sys_bp', 'dia_bp']:
                            visit_data[db_field] = int(value)
                        else:
                            visit_data[db_field] = float(value)
            
            visit = Visit(**visit_data)
            session.add(visit)
            visits_created += 1
        
        # Commit all changes
        session.commit()
        logger.info(f"Migration complete! Created {patients_created} patients and {visits_created} visits")



def main():
    """Main entry point for migration script."""
    # Default CSV path
    csv_path = Path(__file__).parent.parent / "app" / "agent" / "data_temp" / "data.csv"
    
    if not csv_path.exists():
        logger.error(f"CSV file not found at {csv_path}")
        logger.info("Please provide the path to your CSV file")
        return
    
    logger.info("=" * 60)
    logger.info("CSV to Database Migration Script")
    logger.info("=" * 60)
    
    migrate_csv_to_database(csv_path)

    
    logger.info("=" * 60)
    logger.info("Migration completed successfully!")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
