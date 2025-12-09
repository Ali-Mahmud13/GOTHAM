"""
Seed script for comprehensive assessment testing dataset.

Creates 7 demo patients with specific assessment combinations:
- P001: GDM only across 3 visits
- P002: Anemia only across 3 visits  
- P003: FHP only across 2 visits
- P004: GDM + Anemia across 4 visits
- P005: Anemia + FHP across 3 visits
- P006: GDM + Partial Anemia across 3 visits
- P007: All three assessments across 4 visits

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
    session.execute(text('DELETE FROM gdm_assessments'))
    session.execute(text('DELETE FROM anemia_assessments'))
    session.execute(text('DELETE FROM fetal_health_assessments'))
    session.execute(text('DELETE FROM visits'))
    session.execute(text('DELETE FROM patients'))
    session.commit()
    print("  🗑️  All existing data cleared")

# ============================================================================
# P001 - GDM ONLY PATIENT
# ============================================================================
def create_patient_1(session: Session, base_date: datetime):
    """P001: Ayesha Khan - GDM only across 3 visits."""
    print("\n👤 Patient 1: Ayesha Khan (GDM Only)")
    
    patient = Patient(
        patient_identifier="P001",
        name="Ayesha Khan",
        age=28,
        contact_number="+92-300-1234567",
        clinical_notes="GDM screening focus. No anemia concerns. Fetal monitoring via ultrasound only.",
        risk_level="high",
        number_of_pregnancies=1,
        bmi_category=3,
        family_history=True,
        pcos=False,
        unexplained_prenatal_loss=False,
        large_child_or_birth_default=False,
        prediabetes=True
    )
    session.add(patient)
    session.commit()
    
    # Visit 1: Week 12 - Initial GDM screening
    visit1 = Visit(
        patient_id=patient.id,
        visit_date=base_date,
        visit_type="first_trimester",
        notes="Initial GDM screening. Elevated fasting glucose."
    )
    session.add(visit1)
    session.commit()
    
    gdm1 = GDMAssessment(
        visit_id=visit1.id,
        glucose_level=135.0,
        blood_pressure_systolic=125,
        blood_pressure_diastolic=82,
        bmi=29.5,
        ogtt=165.0,
        gestation_weeks=12,
        risk_level=1,  # Elevated
        confidence=0.88,
        ai_report="Elevated fasting glucose detected. OGTT shows borderline values. Recommend dietary modifications and retest."
    )
    session.add(gdm1)
    
    # Visit 2: Week 20 - Follow-up GDM
    visit2 = Visit(
        patient_id=patient.id,
        visit_date=base_date + timedelta(weeks=8),
        visit_type="second_trimester",
        notes="GDM follow-up. Patient on diet control."
    )
    session.add(visit2)
    session.commit()
    
    gdm2 = GDMAssessment(
        visit_id=visit2.id,
        glucose_level=148.0,
        blood_pressure_systolic=128,
        blood_pressure_diastolic=84,
        bmi=30.2,
        ogtt=178.0,
        gestation_weeks=20,
        risk_level=1,  # Elevated
        confidence=0.91,
        ai_report="GDM confirmed. Diet control insufficient. Consider insulin therapy."
    )
    session.add(gdm2)
    
    # Visit 3: Week 28 - GDM management
    visit3 = Visit(
        patient_id=patient.id,
        visit_date=base_date + timedelta(weeks=16),
        visit_type="third_trimester",
        notes="On insulin therapy for GDM."
    )
    session.add(visit3)
    session.commit()
    
    gdm3 = GDMAssessment(
        visit_id=visit3.id,
        glucose_level=122.0,
        blood_pressure_systolic=120,
        blood_pressure_diastolic=80,
        bmi=31.0,
        ogtt=155.0,
        gestation_weeks=28,
        risk_level=0,  # Normal (on treatment)
        confidence=0.94,
        ai_report="Good glucose control on insulin. Continue current regimen."
    )
    session.add(gdm3)
    
    session.commit()
    print("  ✓ 3 visits with GDM assessments created")

# ============================================================================
# P002 - ANEMIA ONLY PATIENT
# ============================================================================
def create_patient_2(session: Session, base_date: datetime):
    """P002: Fatima Ahmed - Anemia only across 3 visits."""
    print("\n👤 Patient 2: Fatima Ahmed (Anemia Only)")
    
    patient = Patient(
        patient_identifier="P002",
        name="Fatima Ahmed",
        age=32,
        contact_number="+92-321-9876543",
        clinical_notes="Iron deficiency anemia. Regular CBC monitoring. No diabetes or fetal concerns.",
        risk_level="medium",
        number_of_pregnancies=2,
        bmi_category=1,
        family_history=False,
        pcos=False,
        unexplained_prenatal_loss=False,
        large_child_or_birth_default=False,
        prediabetes=False
    )
    session.add(patient)
    session.commit()
    
    # Visit 1: Week 10 - Anemia detected
    visit1 = Visit(
        patient_id=patient.id,
        visit_date=base_date,
        visit_type="first_trimester",
        notes="CBC shows low hemoglobin. Iron supplementation started."
    )
    session.add(visit1)
    session.commit()
    
    anemia1 = AnemiaAssessment(
        visit_id=visit1.id,
        wbc=7.2,
        rbc=3.85,
        hgb=9.5,  # Low
        hct=29.0,  # Low
        mcv=75.0,  # Low (microcytic)
        mch=24.7,
        mchc=32.8,
        plt=285.0,
        diagnosis="Iron Deficiency Anemia (IDA)",
        confidence=0.92,
        ai_report="Microcytic hypochromic anemia consistent with iron deficiency. Start oral iron supplementation."
    )
    session.add(anemia1)
    
    # Visit 2: Week 18 - Anemia improving
    visit2 = Visit(
        patient_id=patient.id,
        visit_date=base_date + timedelta(weeks=8),
        visit_type="second_trimester",
        notes="Follow-up CBC. Hemoglobin improving."
    )
    session.add(visit2)
    session.commit()
    
    anemia2 = AnemiaAssessment(
        visit_id=visit2.id,
        wbc=7.5,
        rbc=4.05,
        hgb=10.8,  # Improving
        hct=33.0,
        mcv=81.0,
        mch=26.7,
        mchc=32.7,
        plt=295.0,
        diagnosis="Improving Iron Deficiency Anemia",
        confidence=0.89,
        ai_report="Good response to iron therapy. Continue supplementation."
    )
    session.add(anemia2)
    
    # Visit 3: Week 26 - Anemia resolved
    visit3 = Visit(
        patient_id=patient.id,
        visit_date=base_date + timedelta(weeks=16),
        visit_type="third_trimester",
        notes="CBC normalized."
    )
    session.add(visit3)
    session.commit()
    
    anemia3 = AnemiaAssessment(
        visit_id=visit3.id,
        wbc=7.8,
        rbc=4.30,
        hgb=11.8,  # Normal
        hct=36.5,
        mcv=85.0,  # Normal
        mch=27.4,
        mchc=32.3,
        plt=302.0,
        diagnosis="Resolved Anemia",
        confidence=0.94,
        ai_report="Hemoglobin levels normalized. Continue iron through delivery."
    )
    session.add(anemia3)
    
    session.commit()
    print("  ✓ 3 visits with Anemia assessments created")

# ============================================================================
# P003 - FHP ONLY PATIENT
# ============================================================================
def create_patient_3(session: Session, base_date: datetime):
    """P003: Sana Malik - FHP only across 2 visits."""
    print("\n👤 Patient 3: Sana Malik (FHP Only)")
    
    patient = Patient(
        patient_identifier="P003",
        name="Sana Malik",
        age=26,
        contact_number="+92-333-5551234",
        clinical_notes="Normal pregnancy. CTG monitoring for fetal health assessment only.",
        risk_level="low",
        number_of_pregnancies=1,
        bmi_category=1,
        family_history=False,
        pcos=False,
        unexplained_prenatal_loss=False,
        large_child_or_birth_default=False,
        prediabetes=False
    )
    session.add(patient)
    session.commit()
    
    # Visit 1: Week 28 - First CTG
    visit1 = Visit(
        patient_id=patient.id,
        visit_date=base_date,
        visit_type="third_trimester",
        notes="Routine CTG. All parameters normal."
    )
    session.add(visit1)
    session.commit()
    
    fhp1 = FetalHealthAssessment(
        visit_id=visit1.id,
        baseline_value=140.0,
        accelerations=0.003,
        fetal_movement=0.0,
        uterine_contractions=0.005,
        light_decelerations=0.0,
        severe_decelerations=0.0,
        prolongued_decelerations=0.0,
        abnormal_short_term_variability=50.0,
        mean_value_of_short_term_variability=1.2,
        percentage_of_time_with_abnormal_long_term_variability=15.0,
        mean_value_of_long_term_variability=8.5,
        histogram_width=70.0,
        histogram_min=90.0,
        histogram_max=160.0,
        histogram_number_of_peaks=3.0,
        histogram_number_of_zeroes=0.0,
        histogram_mode=140.0,
        histogram_mean=138.0,
        histogram_median=140.0,
        histogram_variance=25.0,
        histogram_tendency=1.0,
        status=1,  # Normal
        confidence=0.96,
        ai_report="Normal fetal heart rate pattern. No signs of distress."
    )
    session.add(fhp1)
    
    # Visit 2: Week 34 - Follow-up CTG
    visit2 = Visit(
        patient_id=patient.id,
        visit_date=base_date + timedelta(weeks=6),
        visit_type="third_trimester",
        notes="Follow-up CTG. Fetal status remains normal."
    )
    session.add(visit2)
    session.commit()
    
    fhp2 = FetalHealthAssessment(
        visit_id=visit2.id,
        baseline_value=145.0,
        accelerations=0.004,
        fetal_movement=0.0,
        uterine_contractions=0.006,
        light_decelerations=0.0,
        severe_decelerations=0.0,
        prolongued_decelerations=0.0,
        abnormal_short_term_variability=45.0,
        mean_value_of_short_term_variability=1.4,
        percentage_of_time_with_abnormal_long_term_variability=12.0,
        mean_value_of_long_term_variability=9.2,
        histogram_width=75.0,
        histogram_min=95.0,
        histogram_max=170.0,
        histogram_number_of_peaks=3.0,
        histogram_number_of_zeroes=0.0,
        histogram_mode=145.0,
        histogram_mean=142.0,
        histogram_median=145.0,
        histogram_variance=28.0,
        histogram_tendency=1.0,
        status=1,  # Normal
        confidence=0.97,
        ai_report="Continued normal fetal heart rate. Fetal well-being confirmed."
    )
    session.add(fhp2)
    
    session.commit()
    print("  ✓ 2 visits with FHP assessments created")

# ============================================================================
# P004 - GDM + ANEMIA PATIENT
# ============================================================================
def create_patient_4(session: Session, base_date: datetime):
    """P004: Mariam Sheikh - GDM + Anemia across 4 visits."""
    print("\n👤 Patient 4: Mariam Sheikh (GDM + Anemia)")
    
    patient = Patient(
        patient_identifier="P004",
        name="Mariam Sheikh",
        age=30,
        contact_number="+92-345-7778888",
        clinical_notes="Combined GDM and anemia management. High risk pregnancy requiring close monitoring.",
        risk_level="high",
        number_of_pregnancies=2,
        bmi_category=3,
        family_history=True,
        pcos=True,
        unexplained_prenatal_loss=False,
        large_child_or_birth_default=True,
        prediabetes=True
    )
    session.add(patient)
    session.commit()
    
    # Visit 1: Week 10
    visit1 = Visit(
        patient_id=patient.id,
        visit_date=base_date,
        visit_type="first_trimester",
        notes="Both GDM and anemia detected at booking."
    )
    session.add(visit1)
    session.commit()
    
    gdm1 = GDMAssessment(
        visit_id=visit1.id,
        glucose_level=155.0,
        blood_pressure_systolic=132,
        blood_pressure_diastolic=86,
        bmi=31.5,
        ogtt=182.0,
        gestation_weeks=10,
        risk_level=2,  # High
        confidence=0.93,
        ai_report="Early GDM diagnosis. High risk factors present."
    )
    session.add(gdm1)
    
    anemia1 = AnemiaAssessment(
        visit_id=visit1.id,
        wbc=8.2,
        rbc=3.70,
        hgb=9.2,
        hct=28.5,
        mcv=77.0,
        mch=24.9,
        mchc=32.3,
        plt=295.0,
        diagnosis="Iron Deficiency Anemia",
        confidence=0.90,
        ai_report="IDA in context of GDM. Start iron therapy immediately."
    )
    session.add(anemia1)
    
    # Visit 2: Week 18
    visit2 = Visit(
        patient_id=patient.id,
        visit_date=base_date + timedelta(weeks=8),
        visit_type="second_trimester",
        notes="Both conditions being managed."
    )
    session.add(visit2)
    session.commit()
    
    gdm2 = GDMAssessment(
        visit_id=visit2.id,
        glucose_level=142.0,
        blood_pressure_systolic=128,
        blood_pressure_diastolic=84,
        bmi=32.0,
        ogtt=170.0,
        gestation_weeks=18,
        risk_level=1,  # Elevated
        confidence=0.91,
        ai_report="GDM improving with diet. Continue monitoring."
    )
    session.add(gdm2)
    
    anemia2 = AnemiaAssessment(
        visit_id=visit2.id,
        wbc=8.5,
        rbc=3.95,
        hgb=10.5,
        hct=32.0,
        mcv=81.0,
        mch=26.6,
        mchc=32.8,
        plt=305.0,
        diagnosis="Improving Anemia",
        confidence=0.88,
        ai_report="Hemoglobin rising. Continue iron supplementation."
    )
    session.add(anemia2)
    
    # Visit 3: Week 26
    visit3 = Visit(
        patient_id=patient.id,
        visit_date=base_date + timedelta(weeks=16),
        visit_type="third_trimester",
        notes="Insulin started for GDM."
    )
    session.add(visit3)
    session.commit()
    
    gdm3 = GDMAssessment(
        visit_id=visit3.id,
        glucose_level=128.0,
        blood_pressure_systolic=124,
        blood_pressure_diastolic=82,
        bmi=32.8,
        ogtt=158.0,
        gestation_weeks=26,
        risk_level=0,  # Normal (treated)
        confidence=0.94,
        ai_report="Good control on insulin therapy."
    )
    session.add(gdm3)
    
    anemia3 = AnemiaAssessment(
        visit_id=visit3.id,
        wbc=8.8,
        rbc=4.15,
        hgb=11.2,
        hct=34.5,
        mcv=83.0,
        mch=27.0,
        mchc=32.5,
        plt=310.0,
        diagnosis="Mild Anemia",
        confidence=0.86,
        ai_report="Near normal hemoglobin. Maintain iron therapy."
    )
    session.add(anemia3)
    
    # Visit 4: Week 34
    visit4 = Visit(
        patient_id=patient.id,
        visit_date=base_date + timedelta(weeks=24),
        visit_type="third_trimester",
        notes="Both conditions well controlled."
    )
    session.add(visit4)
    session.commit()
    
    gdm4 = GDMAssessment(
        visit_id=visit4.id,
        glucose_level=118.0,
        blood_pressure_systolic=120,
        blood_pressure_diastolic=80,
        bmi=33.2,
        ogtt=145.0,
        gestation_weeks=34,
        risk_level=0,  # Normal
        confidence=0.96,
        ai_report="Excellent glucose control maintained."
    )
    session.add(gdm4)
    
    anemia4 = AnemiaAssessment(
        visit_id=visit4.id,
        wbc=9.0,
        rbc=4.28,
        hgb=11.8,
        hct=36.0,
        mcv=84.0,
        mch=27.6,
        mchc=32.8,
        plt=315.0,
        diagnosis="Resolved Anemia",
        confidence=0.92,
        ai_report="Hemoglobin normalized. Continue iron through delivery."
    )
    session.add(anemia4)
    
    session.commit()
    print("  ✓ 4 visits with GDM + Anemia assessments created")

# ============================================================================
# P005 - ANEMIA + FHP PATIENT
# ============================================================================
def create_patient_5(session: Session, base_date: datetime):
    """P005: Mehreen Hassan - Anemia + FHP across 3 visits."""
    print("\n👤 Patient 5: Mehreen Hassan (Anemia + FHP)")
    
    patient = Patient(
        patient_identifier="P005",
        name="Mehreen Hassan",
        age=29,
        contact_number="+92-311-2223344",
        clinical_notes="Anemia with fetal monitoring. No diabetes concerns.",
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
    session.commit()
    
    # Visit 1: Week 24
    visit1 = Visit(
        patient_id=patient.id,
        visit_date=base_date,
        visit_type="second_trimester",
        notes="Anemia detected. Starting fetal monitoring."
    )
    session.add(visit1)
    session.commit()
    
    anemia1 = AnemiaAssessment(
        visit_id=visit1.id,
        wbc=7.5,
        rbc=3.88,
        hgb=9.8,
        hct=30.0,
        mcv=77.3,
        mch=25.3,
        mchc=32.7,
        plt=288.0,
        diagnosis="Iron Deficiency Anemia",
        confidence=0.91,
        ai_report="Moderate IDA. Start iron supplementation immediately."
    )
    session.add(anemia1)
    
    fhp1 = FetalHealthAssessment(
        visit_id=visit1.id,
        baseline_value=142.0,
        accelerations=0.003,
        fetal_movement=0.0,
        uterine_contractions=0.004,
        light_decelerations=0.001,
        severe_decelerations=0.0,
        prolongued_decelerations=0.0,
        abnormal_short_term_variability=52.0,
        mean_value_of_short_term_variability=1.1,
        percentage_of_time_with_abnormal_long_term_variability=18.0,
        mean_value_of_long_term_variability=8.0,
        histogram_width=68.0,
        histogram_min=88.0,
        histogram_max=156.0,
        histogram_number_of_peaks=2.0,
        histogram_number_of_zeroes=0.0,
        histogram_mode=142.0,
        histogram_mean=140.0,
        histogram_median=142.0,
        histogram_variance=22.0,
        histogram_tendency=1.0,
        status=2,  # Suspect (due to anemia)
        confidence=0.85,
        ai_report="Suspect pattern. May be related to maternal anemia."
    )
    session.add(fhp1)
    
    # Visit 2: Week 30
    visit2 = Visit(
        patient_id=patient.id,
        visit_date=base_date + timedelta(weeks=6),
        visit_type="third_trimester",
        notes="Anemia improving. Fetal status better."
    )
    session.add(visit2)
    session.commit()
    
    anemia2 = AnemiaAssessment(
        visit_id=visit2.id,
        wbc=7.8,
        rbc=4.10,
        hgb=10.9,
        hct=33.5,
        mcv=81.7,
        mch=26.6,
        mchc=32.5,
        plt=295.0,
        diagnosis="Improving Anemia",
        confidence=0.89,
        ai_report="Good response to therapy. Hemoglobin rising."
    )
    session.add(anemia2)
    
    fhp2 = FetalHealthAssessment(
        visit_id=visit2.id,
        baseline_value=144.0,
        accelerations=0.004,
        fetal_movement=0.0,
        uterine_contractions=0.005,
        light_decelerations=0.0,
        severe_decelerations=0.0,
        prolongued_decelerations=0.0,
        abnormal_short_term_variability=48.0,
        mean_value_of_short_term_variability=1.3,
        percentage_of_time_with_abnormal_long_term_variability=14.0,
        mean_value_of_long_term_variability=8.8,
        histogram_width=72.0,
        histogram_min=92.0,
        histogram_max=164.0,
        histogram_number_of_peaks=3.0,
        histogram_number_of_zeroes=0.0,
        histogram_mode=144.0,
        histogram_mean=142.0,
        histogram_median=144.0,
        histogram_variance=26.0,
        histogram_tendency=1.0,
        status=1,  # Normal (improved)
        confidence=0.93,
        ai_report="Fetal status improved with maternal hemoglobin correction."
    )
    session.add(fhp2)
    
    # Visit 3: Week 36
    visit3 = Visit(
        patient_id=patient.id,
        visit_date=base_date + timedelta(weeks=12),
        visit_type="third_trimester",
        notes="Both anemia and fetal status normalized."
    )
    session.add(visit3)
    session.commit()
    
    anemia3 = AnemiaAssessment(
        visit_id=visit3.id,
        wbc=8.0,
        rbc=4.25,
        hgb=11.6,
        hct=35.8,
        mcv=84.2,
        mch=27.3,
        mchc=32.4,
        plt=300.0,
        diagnosis="Resolved Anemia",
        confidence=0.93,
        ai_report="Hemoglobin normalized. Excellent pregnancy outcome expected."
    )
    session.add(anemia3)
    
    fhp3 = FetalHealthAssessment(
        visit_id=visit3.id,
        baseline_value=146.0,
        accelerations=0.004,
        fetal_movement=0.0,
        uterine_contractions=0.006,
        light_decelerations=0.0,
        severe_decelerations=0.0,
        prolongued_decelerations=0.0,
        abnormal_short_term_variability=44.0,
        mean_value_of_short_term_variability=1.5,
        percentage_of_time_with_abnormal_long_term_variability=10.0,
        mean_value_of_long_term_variability=9.5,
        histogram_width=76.0,
        histogram_min=96.0,
        histogram_max=172.0,
        histogram_number_of_peaks=3.0,
        histogram_number_of_zeroes=0.0,
        histogram_mode=146.0,
        histogram_mean=144.0,
        histogram_median=146.0,
        histogram_variance=29.0,
        histogram_tendency=1.0,
        status=1,  # Normal
        confidence=0.97,
        ai_report="Excellent fetal well-being. Ready for delivery."
    )
    session.add(fhp3)
    
    session.commit()
    print("  ✓ 3 visits with Anemia + FHP assessments created")

# ============================================================================
# P006 - GDM + PARTIAL ANEMIA PATIENT
# ============================================================================
def create_patient_6(session: Session, base_date: datetime):
    """P006: Hina Khan - GDM + Partial Anemia across 3 visits."""
    print("\n👤 Patient 6: Hina Khan (GDM + Partial Anemia)")
    
    patient = Patient(
        patient_identifier="P006",
        name="Hina Khan",
        age=27,
        contact_number="+92-333-4445555",
        clinical_notes="GDM with intermittent anemia monitoring. Some CBC data missing in visit 3.",
        risk_level="medium",
        number_of_pregnancies=1,
        bmi_category=2,
        family_history=True,
        pcos=False,
        unexplained_prenatal_loss=False,
        large_child_or_birth_default=False,
        prediabetes=False
    )
    session.add(patient)
    session.commit()
    
    # Visit 1: Week 14 - Complete data
    visit1 = Visit(
        patient_id=patient.id,
        visit_date=base_date,
        visit_type="first_trimester",
        notes="Initial screening. Both GDM and anemia detected."
    )
    session.add(visit1)
    session.commit()
    
    gdm1 = GDMAssessment(
        visit_id=visit1.id,
        glucose_level=138.0,
        blood_pressure_systolic=126,
        blood_pressure_diastolic=82,
        bmi=28.5,
        ogtt=162.0,
        gestation_weeks=14,
        risk_level=1,  # Elevated
        confidence=0.88,
        ai_report="Borderline GDM. Dietary modifications recommended."
    )
    session.add(gdm1)
    
    anemia1 = AnemiaAssessment(
        visit_id=visit1.id,
        wbc=7.6,
        rbc=4.00,
        hgb=10.2,
        hct=31.5,
        mcv=78.8,
        mch=25.5,
        mchc=32.4,
        plt=290.0,
        diagnosis="Mild Anemia",
        confidence=0.87,
        ai_report="Mild IDA. Start prophylactic iron."
    )
    session.add(anemia1)
    
    # Visit 2: Week 22 - Complete data
    visit2 = Visit(
        patient_id=patient.id,
        visit_date=base_date + timedelta(weeks=8),
        visit_type="second_trimester",
        notes="Follow-up. GDM stable, anemia improving."
    )
    session.add(visit2)
    session.commit()
    
    gdm2 = GDMAssessment(
        visit_id=visit2.id,
        glucose_level=132.0,
        blood_pressure_systolic=124,
        blood_pressure_diastolic=80,
        bmi=29.0,
        ogtt=155.0,
        gestation_weeks=22,
        risk_level=0,  # Normal (controlled)
        confidence=0.91,
        ai_report="Good diet control. Continue monitoring."
    )
    session.add(gdm2)
    
    anemia2 = AnemiaAssessment(
        visit_id=visit2.id,
        wbc=7.9,
        rbc=4.18,
        hgb=11.0,
        hct=33.8,
        mcv=80.9,
        mch=26.3,
        mchc=32.5,
        plt=298.0,
        diagnosis="Improving Anemia",
        confidence=0.90,
        ai_report="Hemoglobin rising well."
    )
    session.add(anemia2)
    
    # Visit 3: Week 30 - Partial CBC data  
    visit3 = Visit(
        patient_id=patient.id,
        visit_date=base_date + timedelta(weeks=16),
        visit_type="third_trimester",
        notes="GDM still controlled. Quick CBC - only key parameters measured."
    )
    session.add(visit3)
    session.commit()
    
    gdm3 = GDMAssessment(
        visit_id=visit3.id,
        glucose_level=125.0,
        blood_pressure_systolic=122,
        blood_pressure_diastolic=78,
        bmi=29.8,
        ogtt=148.0,
        gestation_weeks=30,
        risk_level=0,  # Normal
        confidence=0.93,
        ai_report="Excellent GDM control maintained."
    )
    session.add(gdm3)
    
    # Partial Anemia assessment - only essential params
    anemia3 = AnemiaAssessment(
        visit_id=visit3.id,
        wbc=None,  # Not measured
        rbc=None,  # Not measured
        hgb=11.5,  # Measured
        hct=35.0,  # Measured
        mcv=None,  # Not measured
        mch=None,  # Not measured
        mchc=None,  # Not measured
        plt=305.0,  # Measured
        diagnosis="Normal Hemoglobin",
        confidence=0.85,
        ai_report="Key parameters normal. Full CBC not required."
    )
    session.add(anemia3)
    
    session.commit()
    print("  ✓ 3 visits with GDM + Partial Anemia assessments created")

# ============================================================================
# P007 - ALL THREE ASSESSMENTS PATIENT
# ============================================================================
def create_patient_7(session: Session, base_date: datetime):
    """P007: Rabia Mahmood - GDM + Anemia + FHP across 4 visits."""
    print("\n👤 Patient 7: Rabia Mahmood (ALL THREE)")
    
    patient = Patient(
        patient_identifier="P007",
        name="Rabia Mahmood",
        age=31,
        contact_number="+92-300-9998877",
        clinical_notes="High-risk pregnancy requiring comprehensive monitoring. GDM, anemia, and fetal health tracked.",
        risk_level="high",
        number_of_pregnancies=3,
        bmi_category=3,
        family_history=True,
        pcos=True,
        unexplained_prenatal_loss=True,
        large_child_or_birth_default=True,
        prediabetes=True
    )
    session.add(patient)
    session.commit()
    
    # Visit 1: Week 12
    visit1 = Visit(
        patient_id=patient.id,
        visit_date=base_date,
        visit_type="first_trimester",
        notes="High-risk booking. All three monitoring protocols initiated."
    )
    session.add(visit1)
    session.commit()
    
    gdm1 = GDMAssessment(
        visit_id=visit1.id,
        glucose_level=160.0,
        blood_pressure_systolic=135,
        blood_pressure_diastolic=88,
        bmi=32.5,
        ogtt=195.0,
        gestation_weeks=12,
        risk_level=2,  # High
        confidence=0.95,
        ai_report="High GDM risk. Multiple risk factors present."
    )
    session.add(gdm1)
    
    anemia1 = AnemiaAssessment(
        visit_id=visit1.id,
        wbc=8.5,
        rbc=3.65,
        hgb=9.0,
        hct=27.8,
        mcv=76.2,
        mch=24.7,
        mchc=32.4,
        plt=280.0,
        diagnosis="Moderate Iron Deficiency Anemia",
        confidence=0.93,
        ai_report="Significant IDA in high-risk patient. Aggressive iron therapy needed."
    )
    session.add(anemia1)
    
    # No FHP at week 12 (too early for CTG)
    
    # Visit 2: Week 20
    visit2 = Visit(
        patient_id=patient.id,
        visit_date=base_date + timedelta(weeks=8),
        visit_type="second_trimester",
        notes="Mid-pregnancy review. All conditions being actively managed."
    )
    session.add(visit2)
    session.commit()
    
    gdm2 = GDMAssessment(
        visit_id=visit2.id,
        glucose_level=145.0,
        blood_pressure_systolic=130,
        blood_pressure_diastolic=85,
        bmi=33.2,
        ogtt=178.0,
        gestation_weeks=20,
        risk_level=1,  # Elevated
        confidence=0.92,
        ai_report="GDM on diet control. May need insulin soon."
    )
    session.add(gdm2)
    
    anemia2 = AnemiaAssessment(
        visit_id=visit2.id,
        wbc=8.8,
        rbc=3.92,
        hgb=10.3,
        hct=31.5,
        mcv=80.4,
        mch=26.3,
        mchc=32.7,
        plt=292.0,
        diagnosis="Improving Anemia",
        confidence=0.90,
        ai_report="Anemia responding to treatment."
    )
    session.add(anemia2)
    
    # Still too early for reliable CTG
    
    # Visit 3: Week 28 - First CTG
    visit3 = Visit(
        patient_id=patient.id,
        visit_date=base_date + timedelta(weeks=16),
        visit_type="third_trimester",
        notes="Third trimester. All three assessments now active. Insulin started."
    )
    session.add(visit3)
    session.commit()
    
    gdm3 = GDMAssessment(
        visit_id=visit3.id,
        glucose_level=130.0,
        blood_pressure_systolic=126,
        blood_pressure_diastolic=82,
        bmi=34.0,
        ogtt=160.0,
        gestation_weeks=28,
        risk_level=0,  # Normal (on insulin)
        confidence=0.94,
        ai_report="Good control on insulin therapy."
    )
    session.add(gdm3)
    
    anemia3 = AnemiaAssessment(
        visit_id=visit3.id,
        wbc=9.0,
        rbc=4.12,
        hgb=11.0,
        hct=33.8,
        mcv=82.0,
        mch=26.7,
        mchc=32.5,
        plt=300.0,
        diagnosis="Mild Anemia",
        confidence=0.88,
        ai_report="Near-normal hemoglobin. Continue iron."
    )
    session.add(anemia3)
    
    fhp3 = FetalHealthAssessment(
        visit_id=visit3.id,
        baseline_value=138.0,
        accelerations=0.002,
        fetal_movement=0.0,
        uterine_contractions=0.004,
        light_decelerations=0.002,
        severe_decelerations=0.0,
        prolongued_decelerations=0.0,
        abnormal_short_term_variability=55.0,
        mean_value_of_short_term_variability=1.0,
        percentage_of_time_with_abnormal_long_term_variability=20.0,
        mean_value_of_long_term_variability=7.5,
        histogram_width=65.0,
        histogram_min=85.0,
        histogram_max=150.0,
        histogram_number_of_peaks=2.0,
        histogram_number_of_zeroes=0.0,
        histogram_mode=138.0,
        histogram_mean=136.0,
        histogram_median=138.0,
        histogram_variance=20.0,
        histogram_tendency=1.0,
        status=2,  # Suspect (due to maternal conditions)
        confidence=0.82,
        ai_report="Suspect pattern. Likely related to maternal GDM and anemia."
    )
    session.add(fhp3)
    
    # Visit 4: Week 34
    visit4 = Visit(
        patient_id=patient.id,
        visit_date=base_date + timedelta(weeks=22),
        visit_type="third_trimester",
        notes="Pre-delivery monitoring. All parameters improving."
    )
    session.add(visit4)
    session.commit()
    
    gdm4 = GDMAssessment(
        visit_id=visit4.id,
        glucose_level=120.0,
        blood_pressure_systolic=122,
        blood_pressure_diastolic=80,
        bmi=34.5,
        ogtt=148.0,
        gestation_weeks=34,
        risk_level=0,  # Normal
        confidence=0.96,
        ai_report="Excellent glucose control. Ready for delivery planning."
    )
    session.add(gdm4)
    
    anemia4 = AnemiaAssessment(
        visit_id=visit4.id,
        wbc=9.2,
        rbc=4.30,
        hgb=11.8,
        hct=36.2,
        mcv=84.2,
        mch=27.4,
        mchc=32.6,
        plt=308.0,
        diagnosis="Resolved Anemia",
        confidence=0.94,
        ai_report="Hemoglobin normalized. Iron stores adequate for delivery."
    )
    session.add(anemia4)
    
    fhp4 = FetalHealthAssessment(
        visit_id=visit4.id,
        baseline_value=143.0,
        accelerations=0.004,
        fetal_movement=0.0,
        uterine_contractions=0.005,
        light_decelerations=0.0,
        severe_decelerations=0.0,
        prolongued_decelerations=0.0,
        abnormal_short_term_variability=46.0,
        mean_value_of_short_term_variability=1.4,
        percentage_of_time_with_abnormal_long_term_variability=12.0,
        mean_value_of_long_term_variability=9.0,
        histogram_width=74.0,
        histogram_min=94.0,
        histogram_max=168.0,
        histogram_number_of_peaks=3.0,
        histogram_number_of_zeroes=0.0,
        histogram_mode=143.0,
        histogram_mean=141.0,
        histogram_median=143.0,
        histogram_variance=27.0,
        histogram_tendency=1.0,
        status=1,  # Normal (improved)
        confidence=0.95,
        ai_report="Fetal status normalized with maternal condition improvement. Good outcome expected."
    )
    session.add(fhp4)
    
    session.commit()
    print("  ✓ 4 visits with ALL THREE assessments created")

# Main execution
def main():
    print("\\n" + "="*70)
    print("🌱 SEEDING COMPREHENSIVE ASSESSMENT DATABASE")
    print("="*70)
    
    with Session(engine) as session:
        print("\\n🗑️  Clearing existing data...")
        clear_existing_data(session)
        
        base_date = datetime(2024, 8, 15, 10, 30)
        
        create_patient_1(session, base_date)  # GDM only
        create_patient_2(session, base_date)  # Anemia only
        create_patient_3(session, base_date)  # FHP only
        create_patient_4(session, base_date)  # GDM + Anemia
        create_patient_5(session, base_date)  # Anemia + FHP
        create_patient_6(session, base_date)  # GDM + Partial Anemia
        create_patient_7(session, base_date)  # All three
    
    print("\\n" + "="*70)
    print("✅ Seeding complete!")
    print("\\nSummary:")
    
    with Session(engine) as session:
        patients = session.exec(select(Patient)).all()
        visits = session.exec(select(Visit)).all()
        gdm = session.exec(select(GDMAssessment)).all()
        anemia = session.exec(select(AnemiaAssessment)).all()
        fhp = session.exec(select(FetalHealthAssessment)).all()
        
        print(f"  • {len(patients)} patients")
        print(f"  • {len(visits)} visits")
        print(f"  • {len(gdm)} GDM assessments")
        print(f"  • {len(anemia)} Anemia assessments")
        print(f"  • {len(fhp)} Fetal Health assessments")
    
    print("="*70 + "\\n")

if __name__ == "__main__":
    main()
