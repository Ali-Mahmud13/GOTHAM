"""Seed realistic longitudinal clinical history for all existing patients.

What this script does:
- Ensures schema separates visit doctor notes and AI reports.
- Replaces existing visit history for every current patient.
- Generates 3-8 historical visits per patient with realistic spacing.
- Populates GDM, anemia, and fetal assessment fields with trend-consistent values.
- Writes physician notes (observations + plan/recommendations) for each visit.
- Ensures most recent assessment AI reports include risk assessment and management.

Run:
    python scripts/seed_realistic_clinical_history.py
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from random import Random
from typing import List
import hashlib
import sys

from sqlalchemy import inspect, text
from sqlmodel import Session, delete, select

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.db.session import engine
from app.models import AnemiaAssessment, FetalHealthAssessment, GDMAssessment, Patient, Visit


@dataclass
class PatientProfile:
    hypertensive: bool
    diabetic: bool
    anemia_prone: bool
    sedentary: bool


def stable_seed(value: str) -> int:
    """Return deterministic integer seed for a string value."""
    return int(hashlib.sha256(value.encode("utf-8")).hexdigest()[:12], 16)


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def target_risk_for_patient(patient_identifier: str) -> str:
    """Deterministically distribute patients across low/medium/high risk tiers."""
    digits = "".join(ch for ch in patient_identifier if ch.isdigit())
    if digits:
        bucket = int(digits) % 3
    else:
        bucket = stable_seed(patient_identifier) % 3
    if bucket == 0:
        return "high"
    if bucket == 1:
        return "medium"
    return "low"


def ensure_schema_separation(session: Session) -> None:
    """Ensure notes and AI report columns are present and separated."""
    inspector = inspect(engine)

    table_columns = {
        "visits": {c["name"] for c in inspector.get_columns("visits")},
        "gdm_assessments": {c["name"] for c in inspector.get_columns("gdm_assessments")},
        "anemia_assessments": {c["name"] for c in inspector.get_columns("anemia_assessments")},
        "fetal_health_assessments": {c["name"] for c in inspector.get_columns("fetal_health_assessments")},
    }

    if "notes" not in table_columns["visits"]:
        session.execute(text("ALTER TABLE visits ADD COLUMN notes TEXT"))

    # Backward compatibility for older schema where doctor_notes existed.
    if "doctor_notes" in table_columns["visits"] and "notes" in {c["name"] for c in inspect(engine).get_columns("visits")}:
        session.execute(text("UPDATE visits SET notes = COALESCE(notes, doctor_notes)"))

    for table_name in ("gdm_assessments", "anemia_assessments", "fetal_health_assessments"):
        if "ai_report" not in table_columns[table_name]:
            session.execute(text(f"ALTER TABLE {table_name} ADD COLUMN ai_report TEXT"))

    session.commit()


def build_profile(patient: Patient, rng: Random, target_risk: str) -> PatientProfile:
    bmi_cat = patient.bmi_category or 1
    pregnancies = patient.number_of_pregnancies or 1

    if target_risk == "high":
        hypertensive = True
        diabetic = True
        anemia_prone = True
        sedentary = True
    elif target_risk == "medium":
        hypertensive = bool(patient.age >= 35 or bmi_cat >= 2 or rng.random() < 0.55)
        diabetic = bool(patient.prediabetes or patient.family_history or rng.random() < 0.55)
        anemia_prone = bool(pregnancies >= 2 or rng.random() < 0.55)
        sedentary = bool(bmi_cat >= 2 or rng.random() < 0.5)
    else:
        hypertensive = bool(patient.age >= 38 and rng.random() < 0.2)
        diabetic = bool(patient.prediabetes and rng.random() < 0.5)
        anemia_prone = bool(pregnancies >= 3 and rng.random() < 0.35)
        sedentary = bool(bmi_cat >= 3 and rng.random() < 0.4)

    return PatientProfile(
        hypertensive=hypertensive,
        diabetic=diabetic,
        anemia_prone=anemia_prone,
        sedentary=sedentary,
    )


def visit_dates(rng: Random, count: int) -> List[datetime]:
    """Generate realistic historical visit dates in ascending order."""
    last_visit = datetime.now() - timedelta(days=rng.randint(7, 35))
    dates = [last_visit]

    for _ in range(count - 1):
        gap_days = rng.randint(21, 56)
        dates.append(dates[-1] - timedelta(days=gap_days))

    return sorted(dates)


def trimester_for_weeks(weeks: int) -> str:
    if weeks <= 13:
        return "first_trimester"
    if weeks <= 27:
        return "second_trimester"
    return "third_trimester"


def generate_doctor_note(
    patient: Patient,
    profile: PatientProfile,
    gest_weeks: int,
    systolic: int,
    diastolic: int,
    glucose: float,
    hba1c: float,
    hgb: float,
    fetal_baseline: float,
    fetal_status: int,
    medications: List[str],
) -> str:
    """Create realistic physician note with observations and care plan."""
    symptoms = []
    if profile.hypertensive and systolic >= 140:
        symptoms.append("intermittent headache")
    if profile.diabetic and glucose >= 130:
        symptoms.append("post-prandial fatigue")
    if profile.anemia_prone and hgb < 10.8:
        symptoms.append("mild exertional dizziness")
    if not symptoms:
        symptoms.append("no acute maternal complaints")

    fh_cm = gest_weeks - 2 if gest_weeks >= 20 else max(gest_weeks - 1, 8)
    fetal_status_text = {1: "reassuring", 2: "suspect", 3: "pathological"}.get(fetal_status, "reassuring")

    return (
        f"S: Patient at {gest_weeks} weeks reports {', '.join(symptoms)}.\n"
        f"O: BP {systolic}/{diastolic} mmHg, random glucose {glucose:.0f} mg/dL, HbA1c {hba1c:.1f}%, "
        f"Hb {hgb:.1f} g/dL. Fundal height ~{fh_cm} cm. FHR baseline {fetal_baseline:.0f} bpm ({fetal_status_text}).\n"
        f"A: Ongoing antenatal follow-up with focus on {'glycemic control' if profile.diabetic else 'routine metabolic screening'}, "
        f"{'blood-pressure surveillance' if profile.hypertensive else 'normotensive status'}, and "
        f"{'correction of iron stores' if profile.anemia_prone else 'stable hematology profile'}.\n"
        f"P: Continue {', '.join(medications)}. Reinforce diet, hydration, kick-count counseling, and warning signs review. "
        f"Repeat CBC/glucose panel next scheduled visit and adjust treatment based on trend."
    )


def overall_risk_label(profile: PatientProfile, systolic: int, glucose: float, hgb: float, fetal_status: int) -> str:
    score = 0
    if profile.hypertensive and systolic >= 140:
        score += 2
    elif profile.hypertensive:
        score += 1

    if profile.diabetic and glucose >= 140:
        score += 2
    elif profile.diabetic and glucose >= 125:
        score += 1

    if profile.anemia_prone and hgb < 10.5:
        score += 2
    elif profile.anemia_prone and hgb < 11.2:
        score += 1

    if fetal_status >= 2:
        score += 2

    if score >= 5:
        return "high"
    if score >= 3:
        return "medium"
    return "low"


def build_ai_report(domain: str, is_latest: bool, risk: str, details: str, management: str) -> str:
    prefix = "Latest Visit Risk Assessment" if is_latest else "Interim Risk Review"
    return (
        f"{prefix} ({domain.upper()}):\n"
        f"Risk Level: {risk.capitalize()}\n"
        f"Findings: {details}\n"
        f"Management: {management}"
    )


def clear_patient_history(session: Session, patient_id: int) -> None:
    visit_ids = list(session.exec(select(Visit.id).where(Visit.patient_id == patient_id)).all())
    if not visit_ids:
        return

    session.exec(delete(GDMAssessment).where(GDMAssessment.visit_id.in_(visit_ids)))
    session.exec(delete(AnemiaAssessment).where(AnemiaAssessment.visit_id.in_(visit_ids)))
    session.exec(delete(FetalHealthAssessment).where(FetalHealthAssessment.visit_id.in_(visit_ids)))
    session.exec(delete(Visit).where(Visit.id.in_(visit_ids)))


def seed_patient_history(session: Session, patient: Patient) -> int:
    rng = Random(stable_seed(patient.patient_identifier))
    target_risk = target_risk_for_patient(patient.patient_identifier)
    profile = build_profile(patient, rng, target_risk)

    visit_count = rng.randint(3, 8)
    dates = visit_dates(rng, visit_count)

    start_weeks = rng.randint(8, 14)
    first_date = dates[0]

    if target_risk == "high":
        base_sys = rng.randint(148, 162)
        base_dia = rng.randint(94, 104)
        base_glucose = rng.uniform(145, 178)
        base_hba1c = rng.uniform(6.8, 8.2)
        base_hgb = rng.uniform(8.8, 10.2)
    elif target_risk == "medium":
        base_sys = rng.randint(130, 146)
        base_dia = rng.randint(84, 94)
        base_glucose = rng.uniform(112, 145)
        base_hba1c = rng.uniform(5.9, 6.8)
        base_hgb = rng.uniform(10.2, 11.4)
    else:
        base_sys = rng.randint(108, 124)
        base_dia = rng.randint(68, 80)
        base_glucose = rng.uniform(82, 108)
        base_hba1c = rng.uniform(5.1, 5.8)
        base_hgb = rng.uniform(11.2, 12.8)

    created = 0
    latest_note = None
    latest_risk = "low"

    for idx, visit_date in enumerate(dates):
        progress = idx / max(visit_count - 1, 1)
        weeks_delta = max((visit_date - first_date).days // 7, 0)
        gest_weeks = min(start_weeks + weeks_delta, 40)

        # Trend logic: mild improvement over time with care adherence.
        systolic = int(round(base_sys - (8 * progress) + rng.uniform(-3, 3)))
        diastolic = int(round(base_dia - (5 * progress) + rng.uniform(-2, 2)))

        glucose = clamp(base_glucose - (14 * progress) + rng.uniform(-7, 7), 75, 220)
        hba1c = clamp(base_hba1c - (0.7 * progress) + rng.uniform(-0.15, 0.15), 4.8, 10.5)
        bmi = clamp((22 + (patient.bmi_category or 1) * 2.2) + rng.uniform(-0.8, 1.0), 18, 42)
        ogtt = clamp(glucose + rng.uniform(20, 45), 90, 280)
        hdl = clamp(rng.uniform(42, 65) - (5 if profile.diabetic else 0), 30, 75)

        hgb = clamp(base_hgb + (1.1 * progress) + rng.uniform(-0.25, 0.25), 8.0, 14.0)
        hct = clamp(hgb * 3.0 + rng.uniform(-1.2, 1.2), 24, 44)
        rbc = clamp((hgb / 3.1) + rng.uniform(-0.25, 0.2), 2.8, 5.4)
        mcv = clamp((76 if profile.anemia_prone else 84) + (6 * progress) + rng.uniform(-2, 2), 68, 100)
        mch = clamp((24.5 if profile.anemia_prone else 27.5) + (1.8 * progress) + rng.uniform(-0.8, 0.8), 20, 34)
        mchc = clamp(32 + rng.uniform(-1.5, 1.5), 29, 36)
        wbc = clamp(rng.uniform(6.4, 10.8), 4.0, 15.0)
        plt = clamp(rng.uniform(220, 360), 120, 500)

        fetal_baseline = clamp(rng.uniform(132, 152), 110, 180)
        accelerations = clamp(rng.uniform(0.001, 0.007), 0.0, 0.02)
        fetal_movement = clamp(rng.uniform(0.0, 0.012), 0.0, 0.03)

        fetal_status = 1
        if profile.hypertensive and systolic >= 145 and rng.random() < 0.3:
            fetal_status = 2
        if profile.diabetic and glucose >= 155 and rng.random() < 0.15:
            fetal_status = max(fetal_status, 2)

        meds: List[str] = ["prenatal vitamins"]
        if profile.diabetic:
            meds.append("metformin 500 mg BID")
            if glucose > 145:
                meds.append("night-time insulin titration")
        if profile.hypertensive:
            meds.append("labetalol 100 mg BID")
        if profile.anemia_prone:
            meds.append("ferrous sulfate 325 mg daily")

        note = generate_doctor_note(
            patient=patient,
            profile=profile,
            gest_weeks=gest_weeks,
            systolic=systolic,
            diastolic=diastolic,
            glucose=glucose,
            hba1c=hba1c,
            hgb=hgb,
            fetal_baseline=fetal_baseline,
            fetal_status=fetal_status,
            medications=meds,
        )

        visit = Visit(
            patient_id=patient.id,
            visit_date=visit_date,
            visit_type=trimester_for_weeks(gest_weeks),
            notes=note,
            created_at=visit_date,
        )
        session.add(visit)
        session.flush()

        latest = idx == (visit_count - 1)
        overall_risk = overall_risk_label(profile, systolic, glucose, hgb, fetal_status)
        report_risk = target_risk if latest else overall_risk

        gdm_level = 2 if glucose >= 150 else 1 if glucose >= 125 else 0
        gdm_details = (
            f"Glucose {glucose:.0f} mg/dL, OGTT {ogtt:.0f} mg/dL, BP {systolic}/{diastolic} mmHg, "
            f"gestation {gest_weeks} weeks."
        )
        gdm_management = (
            "Continue glucose log, carbohydrate planning, and medication titration with weekly review."
            if gdm_level >= 1
            else "Maintain balanced diet and routine antenatal glucose surveillance."
        )

        session.add(
            GDMAssessment(
                visit_id=visit.id,
                glucose_level=round(glucose, 1),
                blood_pressure_systolic=systolic,
                blood_pressure_diastolic=diastolic,
                bmi=round(bmi, 1),
                hdl=round(hdl, 1),
                ogtt=round(ogtt, 1),
                gestation_weeks=gest_weeks,
                sedentary_lifestyle=profile.sedentary,
                risk_level=gdm_level,
                confidence=None,
                ai_report=build_ai_report(
                    domain="gdm",
                    is_latest=latest,
                    risk=report_risk,
                    details=gdm_details,
                    management=gdm_management,
                ),
                created_at=visit_date,
            )
        )

        anemia_diagnosis = (
            "Iron Deficiency Anemia"
            if hgb < 10.5
            else "Borderline anemia improving"
            if hgb < 11.2
            else "No anemia"
        )
        anemia_details = f"Hb {hgb:.1f} g/dL, Hct {hct:.1f}%, MCV {mcv:.1f} fL, platelets {plt:.0f}."
        anemia_management = (
            "Continue iron therapy and vitamin C co-administration; repeat CBC in 4 weeks."
            if hgb < 11.2
            else "Continue maintenance prenatal iron and routine CBC monitoring."
        )

        session.add(
            AnemiaAssessment(
                visit_id=visit.id,
                wbc=round(wbc, 2),
                rbc=round(rbc, 2),
                hgb=round(hgb, 1),
                hct=round(hct, 1),
                mcv=round(mcv, 1),
                mch=round(mch, 1),
                mchc=round(mchc, 1),
                plt=round(plt, 1),
                diagnosis=anemia_diagnosis,
                confidence=None,
                ai_report=build_ai_report(
                    domain="anemia",
                    is_latest=latest,
                    risk=report_risk,
                    details=anemia_details,
                    management=anemia_management,
                ),
                created_at=visit_date,
            )
        )

        fetal_details = (
            f"Baseline FHR {fetal_baseline:.0f} bpm, accelerations {accelerations:.3f}, "
            f"fetal movement {fetal_movement:.3f}."
        )
        fetal_management = (
            "Increase surveillance frequency and repeat CTG in 48-72 hours with maternal symptom review."
            if fetal_status >= 2
            else "Continue routine antenatal monitoring and daily kick-count education."
        )

        session.add(
            FetalHealthAssessment(
                visit_id=visit.id,
                baseline_value=round(fetal_baseline, 1),
                accelerations=round(accelerations, 4),
                fetal_movement=round(fetal_movement, 4),
                uterine_contractions=round(clamp(rng.uniform(0.001, 0.010), 0.0, 0.03), 4),
                light_decelerations=round(clamp(rng.uniform(0.0, 0.003), 0.0, 0.02), 4),
                severe_decelerations=0.0 if fetal_status == 1 else round(clamp(rng.uniform(0.0, 0.001), 0.0, 0.01), 4),
                prolongued_decelerations=0.0 if fetal_status == 1 else round(clamp(rng.uniform(0.0, 0.001), 0.0, 0.01), 4),
                abnormal_short_term_variability=round(clamp(rng.uniform(20, 55), 0, 100), 1),
                mean_value_of_short_term_variability=round(clamp(rng.uniform(0.7, 2.0), 0.0, 10.0), 2),
                percentage_of_time_with_abnormal_long_term_variability=round(clamp(rng.uniform(8, 28), 0, 100), 1),
                mean_value_of_long_term_variability=round(clamp(rng.uniform(6, 14), 0, 30), 1),
                histogram_width=round(clamp(rng.uniform(55, 95), 10, 180), 1),
                histogram_min=round(clamp(fetal_baseline - rng.uniform(35, 55), 50, 200), 1),
                histogram_max=round(clamp(fetal_baseline + rng.uniform(20, 35), 80, 220), 1),
                histogram_number_of_peaks=rng.randint(1, 6),
                histogram_number_of_zeroes=rng.randint(0, 2),
                histogram_mode=round(clamp(fetal_baseline + rng.uniform(-4, 4), 80, 200), 1),
                histogram_mean=round(clamp(fetal_baseline + rng.uniform(-4, 4), 80, 200), 1),
                histogram_median=round(clamp(fetal_baseline + rng.uniform(-3, 3), 80, 200), 1),
                histogram_variance=round(clamp(rng.uniform(8, 45), 0, 200), 1),
                histogram_tendency=rng.choice([-1, 0, 1]),
                status=fetal_status,
                confidence=None,
                ai_report=build_ai_report(
                    domain="fetal",
                    is_latest=latest,
                    risk=report_risk,
                    details=fetal_details,
                    management=fetal_management,
                ),
                created_at=visit_date,
            )
        )

        created += 1
        if latest:
            latest_note = note
            latest_risk = target_risk

    patient.clinical_notes = latest_note
    patient.risk_level = latest_risk
    patient.updated_at = dates[-1]
    session.add(patient)

    return created


def run() -> None:
    with Session(engine) as session:
        ensure_schema_separation(session)

        patients = list(session.exec(select(Patient).order_by(Patient.patient_identifier)).all())
        if not patients:
            print("No patients found. Add patients first, then rerun this script.")
            return

        print(f"Found {len(patients)} existing patients. Regenerating longitudinal history...")

        total_visits = 0
        for patient in patients:
            clear_patient_history(session, patient.id)
            count = seed_patient_history(session, patient)
            total_visits += count
            print(f"  - {patient.patient_identifier} ({patient.name}): {count} visits seeded")

        session.commit()

        print("\nSeeding complete.")
        print(f"Patients processed: {len(patients)}")
        print(f"Visits created: {total_visits}")
        print("Each patient now has 3-8 timestamped historical visits with doctor notes and AI reports.")


if __name__ == "__main__":
    run()
