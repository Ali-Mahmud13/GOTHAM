from sqlmodel import Session, create_engine, select
from app.models.appointments import Appointment
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL)
with Session(engine) as session:
    appts = session.exec(select(Appointment).limit(5)).all()
    for a in appts:
        print(f"ID: {a.id}, Created At: {a.created_at}, Status: {a.status}, Doctor ID: {a.doctor_id}")
