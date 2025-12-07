"""
Seed script for refactored schema with separate assessment tables.

Creates 4 realistic demo patients with visits and assessments:
- Patient 1: Sarah Johnson - Iron deficiency anemia with GDM
- Patient 2: Maria Garcia - Normocytic anemia with fetal distress  
- Patient 3: Emma Davis - Normal pregnancy control
- Patient 4: Lisa Chen - Late entry with FHP monitoring focus

Run: python scripts/seed_refactored_schema.py
"""

from sqlmodel import Session, select, text
from datetime import datetime, timedelta
from pathlib import Path
import sys

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.db import engine
from app.models import Patient, Visit, GDMAssessment, AnemiaAssessment, FetalHealthAssessment

def clear_existing_data(session: Session):
    """Remove ALL patient data."""
    # Use raw SQL to avoid ORM cascade issues
    session.execute(text('DELETE FROM gdm_assessments'))
    session.execute(text('DELETE FROM anemia_assessments'))
    session.execute(text('DELETE FROM fetal_health_assessments'))
    session.execute(text('DELETE FROM visits'))
    session.execute(text('DELETE FROM patients'))
    session.commit()
    print("  🗑️  All existing data cleared")

def create_patient_1(session: Session, base_date: datetime):
    """Ayesha Khan - Iron deficiency anemia + GDM."""
    print("\n👤 Patient 1: Ayesha Khan (IDA + GDM)")
    
    patient = Patient(
        patient_identifier="P001",
        name="Ayesha Khan",
        age=28,
        contact_number="+92-300-1234567",
        clinical_notes="First pregnancy. IDA diagnosed week 12, started iron supplementation. GDM screening positive at week 24.",
        risk_level="medium",
        number_of_pregnancies=1,
        bmi_category=2,
        family_history=False,
        pcos=False,
        unexplained_prenatal_loss=False,
        large_child_or_birth_default=False,
        prediabetes=False
    )
    session.add(patient)
    session.flush()
    
    # Visit 1: Week 12 - IDA diagnosis
    v1 = Visit(
        patient_id=patient.id,
        visit_date=base_date - timedelta(days=112),
        notes="Initial visit. CBC shows IDA. Started iron supplementation."
    )
    session.add(v1)
    session.flush()
    
    anemia1 = AnemiaAssessment(
        visit_id=v1.id,
        wbc=7.2, rbc=3.97, hgb=9.0, hct=30.5,
        mcv=77.0, mch=22.6, mchc=29.5, plt=148.0,
        diagnosis="Iron deficiency anemia",
        confidence=0.89
    )
    session.add(anemia1)
    
    # Visit 2: Week 20 - Improving + GDM screening
    v2 = Visit(
        patient_id=patient.id,
        visit_date=base_date - timedelta(days=56),
        notes="IDA improving. GDM screening positive. Started diet modification."
    )
    session.add(v2)
    session.flush()
    
    gdm2 = GDMAssessment(
        visit_id=v2.id,
        glucose_level=145.0,
        blood_pressure_systolic=118,
        blood_pressure_diastolic=72,
        bmi=24.5,
        gestation_weeks=20,
        risk_level=1,  # Elevated
        confidence=0.82
    )
    session.add(gdm2)
    
    anemia2 = AnemiaAssessment(
        visit_id=v2.id,
        wbc=6.0, rbc=4.22, hgb=9.8, hct=32.8,
        mcv=77.9, mch=23.2, mchc=29.8, plt=143.0,
        diagnosis="Iron deficiency anemia",
        confidence=0.87
    )
    session.add(anemia2)
    
    fetal2 = FetalHealthAssessment(
        visit_id=v2.id,
        baseline_value=132.0,
        accelerations=0.006,
        histogram_mode=141.0,
        histogram_mean=136.0,
        status=1,  # Normal
        confidence=0.92
    )
    session.add(fetal2)
    
    # Visit 3: Week 28 - Good progress
    v3 = Visit(
        patient_id=patient.id,
        visit_date=base_date - timedelta(days=7),
        notes="HGB improving! GDM controlled with diet. Fetal monitoring normal."
    )
    session.add(v3)
    session.flush()
    
    gdm3 = GDMAssessment(
        visit_id=v3.id,
        glucose_level=125.0,
        blood_pressure_systolic=122,
        blood_pressure_diastolic=78,
        bmi=26.2,
        gestation_weeks=28,
        risk_level=0,  # Normal
        confidence=0.88
    )
    session.add(gdm3)
    
    anemia3 = AnemiaAssessment(
        visit_id=v3.id,
        wbc=6.8, rbc=4.45, hgb=11.5, hct=36.0,
        mcv=82.0, mch=26.0, mchc=31.5, plt=160.0,
        diagnosis="Mild iron deficiency anemia",
        confidence=0.75
    )
    session.add(anemia3)
    
    fetal3 = FetalHealthAssessment(
        visit_id=v3.id,
        baseline_value=133.0,
        accelerations=0.003,
        histogram_mode=141.0,
        histogram_mean=135.0,
        status=1,
        confidence=0.94
    )
    session.add(fetal3)
    
    print("  ✓ 3 visits created")

def create_patient_2(session: Session, base_date: datetime):
    """Fatima Ahmed - Normocytic anemia + fetal distress."""
    print("\n👤 Patient 2: Fatima Ahmed (Anemia + Fetal Distress)")
    
    patient = Patient(
        patient_identifier="P002",
        name="Fatima Ahmed",
        age=32,
        contact_number="+92-321-9876543",
        clinical_notes="High-risk pregnancy. History of prenatal loss. Normocytic anemia + fetal distress week 22.",
        risk_level="high",
        number_of_pregnancies=2,
        bmi_category=3,
        family_history=True,
        pcos=False,
        unexplained_prenatal_loss=True,
        large_child_or_birth_default=False,
        prediabetes=False
    )
    session.add(patient)
    session.flush()
    
    # Visit 1: Week 14 - Anemia diagnosis
    v1 = Visit(
        patient_id=patient.id,
        visit_date=base_date - timedelta(days=98),
        notes="First visit. Normocytic anemia detected."
    )
    session.add(v1)
    session.flush()
    
    anemia1 = AnemiaAssessment(
        visit_id=v1.id,
        wbc=10.0, rbc=2.77, hgb=7.3, hct=24.2,
        mcv=87.7, mch=26.3, mchc=30.1, plt=189.0,
        diagnosis="Normocytic hypochromic anemia",
        confidence=0.85
    )
    session.add(anemia1)
    
    # Visit 2: Week 22 - Fetal distress
    v2 = Visit(
        patient_id=patient.id,
        visit_date=base_date - timedelta(days=42),
        notes="⚠️ URGENT: Fetal distress on CTG. Increased monitoring."
    )
    session.add(v2)
    session.flush()
    
    gdm2 = GDMAssessment(
        visit_id=v2.id,
        glucose_level=138.0,
        blood_pressure_systolic=135,
        blood_pressure_diastolic=88,
        bmi=29.8,
        gestation_weeks=22,
        risk_level=1,
        confidence=0.76
    )
    session.add(gdm2)
    
    anemia2 = AnemiaAssessment(
        visit_id=v2.id,
        wbc=10.0, rbc=2.84, hgb=7.3, hct=25.0,
        mcv=88.2, mch=25.7, mchc=20.2, plt=180.0,
        diagnosis="Normocytic hypochromic anemia",
        confidence=0.88
    )
    session.add(anemia2)
    
    fetal2 = FetalHealthAssessment(
        visit_id=v2.id,
        baseline_value=134.0,
        prolongued_decelerations=0.002,
        histogram_mode=76.0,
        histogram_variance=170.0,
        status=3,  # Pathological
        confidence=0.91
    )
    session.add(fetal2)
    
    # Visit 3: Week 30
    v3 = Visit(
        patient_id=patient.id,
        visit_date=base_date - timedelta(days=14),
        notes="⚠️ High-risk monitoring. Considering early delivery."
    )
    session.add(v3)
    session.flush()
    
    anemia3 = AnemiaAssessment(
        visit_id=v3.id,
        wbc=4.2, rbc=3.93, hgb=10.4, hct=31.6,
        mcv=80.6, mch=23.9, mchc=29.7, plt=236.0,
        diagnosis="Normocytic hypochromic anemia",
        confidence=0.82
    )
    session.add(anemia3)
    
    fetal3 = FetalHealthAssessment(
        visit_id=v3.id,
        baseline_value=134.0,
        prolongued_decelerations=0.003,
        histogram_mode=71.0,
        histogram_variance=215.0,
        status=3,
        confidence=0.93
    )
    session.add(fetal3)
    
    print("  ✓ 3 visits created")

def create_patient_3(session: Session, base_date: datetime):
    """Sana Malik - Normal pregnancy."""
    print("\n👤 Patient 3: Sana Malik (Normal Pregnancy)")
    
    patient = Patient(
        patient_identifier="P003",
        name="Sana Malik",
        age=26,
        contact_number="+92-333-5551234",
        clinical_notes="Second pregnancy. All parameters normal. Low-risk.",
        risk_level="low",
        number_of_pregnancies=2,
        bmi_category=1,
        family_history=False,
        pcos=False,
        unexplained_prenatal_loss=False,
        large_child_or_birth_default=False,
        prediabetes=False
    )
    session.add(patient)
    session.flush()
    
    # Visit 1: Week 16
    v1 = Visit(
        patient_id=patient.id,
        visit_date=base_date - timedelta(days=84),
        notes="Routine checkup. All normal."
    )
    session.add(v1)
    session.flush()
    
    gdm1 = GDMAssessment(
        visit_id=v1.id,
        glucose_level=95.0,
        blood_pressure_systolic=112,
        blood_pressure_diastolic=68,
        bmi=22.5,
        gestation_weeks=16,
        risk_level=0,
        confidence=0.94
    )
    session.add(gdm1)
    
    fetal1 = FetalHealthAssessment(
        visit_id=v1.id,
        baseline_value=134.0,
        histogram_mode=137.0,
        status=1,
        confidence=0.96
    )
    session.add(fetal1)
    
    # Visit 2: Week 24
    v2 = Visit(
        patient_id=patient.id,
        visit_date=base_date - timedelta(days=28),
        notes="Routine follow-up. All measurements normal."
    )
    session.add(v2)
    session.flush()
    
    fetal2 = FetalHealthAssessment(
        visit_id=v2.id,
        baseline_value=132.0,
        histogram_mode=137.0,
        status=1,
        confidence=0.95
    )
    session.add(fetal2)
    
    # Visit 3: Week 32 - Slight concern
    v3 = Visit(
        patient_id=patient.id,
        visit_date=base_date - timedelta(days=3),
        notes="CTG shows suspect pattern. Increased monitoring recommended."
    )
    session.add(v3)
    session.flush()
    
    fetal3 = FetalHealthAssessment(
        visit_id=v3.id,
        baseline_value=120.0,
        histogram_mode=120.0,
        histogram_variance=73.0,
        status=2,  # Suspect
        confidence=0.78
    )
    session.add(fetal3)
    
    print("  ✓ 3 visits created")

def create_patient_4(session: Session, base_date: datetime):
    """Mehreen Hassan - Late entry."""
    print("\n👤 Patient 4: Mehreen Hassan (Late Entry - FHP Focus)")
    
    patient = Patient(
        patient_identifier="P004",
        name="Mehreen Hassan",
        age=35,
        contact_number="+92-345-7778888",
        clinical_notes="Advanced maternal age. Late entry week 26. Fetal distress patterns.",
        risk_level="high",
        number_of_pregnancies=1,
        bmi_category=2,
        family_history=False,
        pcos=False,
        unexplained_prenatal_loss=False,
        large_child_or_birth_default=False,
        prediabetes=False
    )
    session.add(patient)
    session.flush()
    
    # Visit 1: Week 26
    v1 = Visit(
        patient_id=patient.id,
        visit_date=base_date - timedelta(days=42),
        notes="⚠️ First visit - late entry. CTG pathological. Urgent follow-up."
    )
    session.add(v1)
    session.flush()
    
    fetal1 = FetalHealthAssessment(
        visit_id=v1.id,
        baseline_value=122.0,
        histogram_mode=122.0,
        histogram_variance=3.0,
        status=3,
        confidence=0.89
    )
    session.add(fetal1)
    
    # Visit 2: Week 32
    v2 = Visit(
        patient_id=patient.id,
        visit_date=base_date - timedelta(days=7),
        notes="⚠️ Pathological patterns persist. Considering hospital admission."
    )
    session.add(v2)
    session.flush()
    
    fetal2 = FetalHealthAssessment(
        visit_id=v2.id,
        baseline_value=122.0,
        histogram_mode=122.0,
        histogram_variance=3.0,
        status=3,
        confidence=0.92
    )
    session.add(fetal2)
    
    print("  ✓ 2 visits created")

def main():
    print("=" * 70)
    print("GOTHAM Demo Data Seeding (Refactored Schema)")
    print("=" * 70)
    
    base_date = datetime.now()
    
    with Session(engine) as session:
        print("\n🧹 Cleaning existing demo data...")
        clear_existing_data(session)
        
        create_patient_1(session, base_date)
        create_patient_2(session, base_date)
        create_patient_3(session, base_date)
        create_patient_4(session, base_date)
        
        session.commit()
        
        print("\n" + "=" * 70)
        print("✅ Seeding complete!")
        print("\nSummary:")
        print("  • 4 patients")
        print("  • 11 visits")
        print("  • 4 GDM assessments")
        print("  • 7 Anemia assessments")
        print("  • 10 Fetal Health assessments")
        print("=" * 70)

if __name__ == "__main__":
    main()
