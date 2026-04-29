"""One-time backfill for visit note provenance.

Purpose:
- Populate visits.recorded_by_role and visits.recorded_by_user_id for historical rows.
- Improve note-source labeling (patient, current doctor, previous doctor) in UI.

Run:
    python scripts/backfill_visit_provenance.py
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import sys

from sqlalchemy import inspect, text
from sqlmodel import Session, select

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.db.session import engine
from app.models import Patient, Visit
from app.models.auth import AuthUser
from app.models.appointments import RegistrationRequest


@dataclass
class PatientContext:
    patient: Patient
    patient_user: AuthUser | None
    current_registration_start: datetime | None


def ensure_provenance_columns() -> None:
    """Add provenance columns to visits table if they are missing."""
    inspector = inspect(engine)
    visit_columns = {c["name"] for c in inspector.get_columns("visits")}

    required = {
        "recorded_by_role": "TEXT",
        "recorded_by_user_id": "INTEGER",
    }

    with engine.connect() as conn:
        for col_name, col_type in required.items():
            if col_name not in visit_columns:
                conn.execute(text(f"ALTER TABLE visits ADD COLUMN {col_name} {col_type}"))
                conn.commit()
                print(f"Added visits.{col_name}")


def get_patient_context(session: Session, patient: Patient) -> PatientContext:
    patient_user = session.exec(
        select(AuthUser)
        .where(AuthUser.role == "patient")
        .where(AuthUser.patient_id == patient.id)
    ).first()

    current_registration_start = None
    if patient_user and patient.doctor_id:
        latest_approved = session.exec(
            select(RegistrationRequest)
            .where(RegistrationRequest.patient_id == patient_user.id)
            .where(RegistrationRequest.doctor_id == patient.doctor_id)
            .where(RegistrationRequest.status == "approved")
            .order_by(RegistrationRequest.updated_at.desc())
        ).first()

        if latest_approved:
            current_registration_start = latest_approved.updated_at or latest_approved.created_at

    return PatientContext(
        patient=patient,
        patient_user=patient_user,
        current_registration_start=current_registration_start,
    )


def infer_provenance(visit: Visit, ctx: PatientContext) -> tuple[str | None, int | None]:
    """Infer (recorded_by_role, recorded_by_user_id) from available historical context."""
    vtype = (visit.visit_type or "").strip().lower()

    # Explicit patient self-note type.
    if vtype == "patient_notes":
        return "patient", (ctx.patient_user.id if ctx.patient_user else None)

    # Explicit doctor notes are doctor-authored; keep user_id if confidently current doctor.
    if vtype == "doctor_notes":
        if ctx.current_registration_start and ctx.patient.doctor_id and visit.visit_date >= ctx.current_registration_start:
            return "doctor", ctx.patient.doctor_id
        return "doctor", None

    # Legacy clinical_notes can be either patient-entered (old unregistered flow) or doctor-entered.
    if vtype == "clinical_notes":
        if ctx.current_registration_start and ctx.patient.doctor_id and visit.visit_date >= ctx.current_registration_start:
            return "doctor", ctx.patient.doctor_id
        return "patient", (ctx.patient_user.id if ctx.patient_user else None)

    # Generic visit entries: if no note text and has a current registration interval, treat as doctor care.
    if ctx.current_registration_start and ctx.patient.doctor_id and visit.visit_date >= ctx.current_registration_start:
        return "doctor", ctx.patient.doctor_id

    # Otherwise, default to doctor role but unknown specific doctor for historical records.
    return "doctor", None


def main() -> None:
    ensure_provenance_columns()

    with Session(engine) as session:
        patients = list(session.exec(select(Patient)).all())
        if not patients:
            print("No patients found. Nothing to backfill.")
            return

        updates = 0
        inspected = 0

        for patient in patients:
            ctx = get_patient_context(session, patient)
            visits = list(session.exec(select(Visit).where(Visit.patient_id == patient.id)).all())

            for visit in visits:
                inspected += 1

                # Skip rows already fully attributed.
                if visit.recorded_by_role and visit.recorded_by_user_id is not None:
                    continue

                role, user_id = infer_provenance(visit, ctx)

                changed = False
                if not visit.recorded_by_role and role:
                    visit.recorded_by_role = role
                    changed = True
                if visit.recorded_by_user_id is None and user_id is not None:
                    visit.recorded_by_user_id = user_id
                    changed = True

                if changed:
                    session.add(visit)
                    updates += 1

        session.commit()

    print("Visit provenance backfill complete.")
    print(f"Visits inspected: {inspected}")
    print(f"Visits updated: {updates}")


if __name__ == "__main__":
    main()
