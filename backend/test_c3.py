from sqlmodel import Session, select, create_engine, func
from sqlalchemy import cast, Integer

engine = create_engine("sqlite:///medical_agent.db")

from app.models.patient import Patient

with Session(engine) as session:
    max_id = session.exec(
        select(func.max(cast(func.substr(Patient.patient_identifier, 2), Integer)))
        .where(Patient.patient_identifier.like("P%"))
    ).one()
    
    print(f"Max ID: {max_id}")
    max_num = max_id or 0
    print(f"Next ID: P{max_num + 1:03d}")
