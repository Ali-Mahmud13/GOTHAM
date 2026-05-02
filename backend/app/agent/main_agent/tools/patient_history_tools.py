from langchain_core.tools import tool
from sqlmodel import Session, select
from app.db.session import engine
from app.models.patient import Patient, Visit
from app.models.assessments import GDMAssessment, AnemiaAssessment, FetalHealthAssessment

@tool
def get_full_patient_history(patient_id: str) -> str:
    """
    Extract the complete longitudinal history of a patient, including demographics, past visits, and past assessment results.
    Use this to get a deep understanding of a patient's historical trends.
    """
    with Session(engine) as session:
        # Resolve patient by ID or identifier string
        if patient_id.isdigit():
            patient = session.get(Patient, int(patient_id))
        else:
            patient = session.exec(select(Patient).where(Patient.patient_identifier == patient_id)).first()
            
        if not patient:
            return f"Patient {patient_id} not found."
            
        history = [
            f"=== PATIENT PROFILE ===",
            f"Name: {patient.name} (ID: {patient.patient_identifier})",
            f"Age: {patient.age}, BMI Category: {patient.bmi_category}",
            f"Risk Level: {patient.risk_level}",
            f"Pregnancies: {patient.number_of_pregnancies}",
            f"Family History of Diabetes: {patient.family_history}",
            f"PCOS: {patient.pcos}",
            f"Prediabetes: {patient.prediabetes}",
            f"History of Unexplained Loss: {patient.unexplained_prenatal_loss}",
            f"History of Large Child/Complications: {patient.large_child_or_birth_default}",
            f"Clinical Notes: {patient.clinical_notes or 'None'}\n"
        ]
        
        visits = session.exec(
            select(Visit)
            .where(Visit.patient_id == patient.id)
            .order_by(Visit.visit_date)
        ).all()
        
        if not visits:
            history.append("No past visits recorded.")
            return "\n".join(history)
            
        history.append("=== PAST VISITS & ASSESSMENTS ===")
        for i, visit in enumerate(visits):
            history.append(f"\n--- Visit {i+1}: {visit.visit_date.strftime('%Y-%m-%d')} ({visit.visit_type or 'Routine'}) ---")
            if visit.notes:
                history.append(f"Notes: {visit.notes}")
                
            # GDM
            if visit.gdm_assessment:
                gdm = visit.gdm_assessment
                history.append(f"[GDM Assessment] Risk Level: {gdm.risk_level}, Glucose: {gdm.glucose_level}, BP: {gdm.blood_pressure_systolic}/{gdm.blood_pressure_diastolic}")
                if gdm.ai_report:
                    history.append(f"  AI Report: {gdm.ai_report}")
                    
            # Anemia
            if visit.anemia_assessment:
                anemia = visit.anemia_assessment
                history.append(f"[Anemia Assessment] Diagnosis: {anemia.diagnosis}, HGB: {anemia.hgb}, RBC: {anemia.rbc}, WBC: {anemia.wbc}")
                if anemia.ai_report:
                    history.append(f"  AI Report: {anemia.ai_report}")
                    
            # Fetal Health
            if visit.fetal_health_assessment:
                fetal = visit.fetal_health_assessment
                history.append(f"[Fetal Health Assessment] Status: {fetal.status}, Baseline HR: {fetal.baseline_value}, Accelerations: {fetal.accelerations}")
                if fetal.ai_report:
                    history.append(f"  AI Report: {fetal.ai_report}")
                    
        return "\n".join(history)
