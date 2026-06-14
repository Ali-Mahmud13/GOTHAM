from datetime import datetime, timedelta

from sqlmodel import Session, SQLModel, create_engine, select

from app.models import (
    AnemiaAssessment,
    FetalHealthAssessment,
    GDMAssessment,
    Patient,
    PatientRiskHistory,
    Visit,
)
from app.services import assessment_persistence
from app.agent.main_agent.model_results import attach_input_metadata
from app.services.patient_service import PatientService
from app.services.risk_service import (
    anemia_severity,
    highest_risk,
    recompute_patient_risk,
)


def _memory_session() -> Session:
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    return Session(engine)


def _patient() -> Patient:
    return Patient(
        patient_identifier="P999",
        name="Risk Test",
        age=30,
        contact_number="000",
    )


def test_highest_risk_is_order_independent():
    assert highest_risk(["low", "high", "medium"]) == "high"
    assert highest_risk(["medium", "low"]) == "medium"
    assert highest_risk([]) == "unassessed"


def test_any_non_healthy_anemia_diagnosis_is_high():
    assert anemia_severity("Healthy") == "low"
    assert anemia_severity("Iron deficiency anemia") == "high"
    assert anemia_severity("Leukemia with thrombocytopenia") == "high"


def test_partial_low_result_does_not_erase_latest_high_domain():
    with _memory_session() as session:
        patient = _patient()
        session.add(patient)
        session.flush()

        maternal_visit = Visit(patient_id=patient.id, visit_date=datetime.utcnow())
        fetal_visit = Visit(
            patient_id=patient.id,
            visit_date=datetime.utcnow() + timedelta(minutes=1),
        )
        session.add(maternal_visit)
        session.add(fetal_visit)
        session.flush()

        session.add(
            GDMAssessment(
                visit_id=maternal_visit.id,
                prediction_status="completed",
                severity="high",
                risk_level=2,
            )
        )
        session.add(
            FetalHealthAssessment(
                visit_id=fetal_visit.id,
                prediction_status="completed",
                severity="low",
                status=1,
            )
        )
        session.flush()

        assert recompute_patient_risk(
            session,
            patient,
            record_history=False,
        ) == "high"


def test_incomplete_new_result_does_not_replace_valid_result():
    with _memory_session() as session:
        patient = _patient()
        session.add(patient)
        session.flush()
        old_visit = Visit(patient_id=patient.id, visit_date=datetime.utcnow())
        new_visit = Visit(
            patient_id=patient.id,
            visit_date=datetime.utcnow() + timedelta(minutes=1),
        )
        session.add(old_visit)
        session.add(new_visit)
        session.flush()
        session.add(
            GDMAssessment(
                visit_id=old_visit.id,
                prediction_status="completed",
                severity="high",
                risk_level=2,
            )
        )
        session.add(
            GDMAssessment(
                visit_id=new_visit.id,
                prediction_status="incomplete",
                severity=None,
            )
        )
        session.flush()

        assert recompute_patient_risk(
            session,
            patient,
            record_history=False,
        ) == "high"


def test_freshness_boundaries():
    now = datetime.utcnow()
    assert PatientService._freshness(now - timedelta(days=30))[1] == "fresh"
    assert PatientService._freshness(now - timedelta(days=31))[1] == "aging"
    assert PatientService._freshness(now - timedelta(days=90))[1] == "aging"
    assert PatientService._freshness(now - timedelta(days=91))[1] == "stale"


def test_input_provenance_matching_is_case_insensitive():
    result = attach_input_metadata(
        {"status": "completed"},
        {"WBC": 8.1},
        {
            "_input_provenance": {
                "WBC": {"age_days": 91, "freshness": "stale"}
            }
        },
    )
    assert result["input_provenance"]["WBC"]["freshness"] == "stale"
    assert result["oldest_input_age_days"] == 91
    assert result["has_stale_inputs"] is True


def test_ctg_fields_are_not_combined_across_visits():
    with _memory_session() as session:
        patient = _patient()
        session.add(patient)
        session.flush()
        older = Visit(
            patient_id=patient.id,
            visit_date=datetime.utcnow() - timedelta(days=1),
        )
        newer = Visit(patient_id=patient.id, visit_date=datetime.utcnow())
        session.add(older)
        session.add(newer)
        session.flush()
        session.add(
            FetalHealthAssessment(
                visit_id=older.id,
                baseline_value=120,
                accelerations=0.01,
            )
        )
        session.add(
            FetalHealthAssessment(
                visit_id=newer.id,
                baseline_value=140,
                fetal_movement=0.02,
            )
        )
        session.flush()

        snapshot = PatientService()._build_prediction_snapshot(
            session,
            patient,
            newer,
        )

        assert snapshot["baseline_value"] == 140
        assert snapshot["fetal_movement"] == 0.02
        assert "accelerations" not in snapshot
        groups = {
            source.get("recording_group")
            for key, source in snapshot["_input_provenance"].items()
            if key in {"baseline_value", "fetal_movement"}
        }
        assert groups == {f"ctg-visit-{newer.id}"}


def test_structured_persistence_writes_confidence_and_one_history_event():
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        patient = _patient()
        session.add(patient)
        session.flush()
        visit = Visit(patient_id=patient.id, visit_date=datetime.utcnow())
        session.add(visit)
        session.commit()

    original_engine = assessment_persistence.engine
    assessment_persistence.engine = engine
    try:
        assert assessment_persistence.save_assessment_report(
            patient_identifier="P999",
            assessment_type="maternal",
            assessment_report="Structured report",
            model_results={
                "gdm": {
                    "status": "completed",
                    "severity": "high",
                    "outcome": "High Risk of Gestational Diabetes",
                    "predicted_class": "positive",
                    "confidence": 0.87,
                    "probabilities": {
                        "no_gestational_diabetes": 0.13,
                        "gestational_diabetes": 0.87,
                    },
                    "input_snapshot": {"ogtt": 180},
                    "input_provenance": {
                        "ogtt": {"freshness": "fresh", "age_days": 2}
                    },
                    "oldest_input_age_days": 2,
                    "has_stale_inputs": False,
                }
            },
        )
    finally:
        assessment_persistence.engine = original_engine

    with Session(engine) as session:
        result = session.exec(select(GDMAssessment)).one()
        histories = session.exec(select(PatientRiskHistory)).all()
        patient = session.exec(select(Patient)).one()
        assert result.prediction_status == "completed"
        assert result.confidence == 0.87
        assert result.probabilities["gestational_diabetes"] == 0.87
        assert patient.risk_level == "high"
        assert len(histories) == 1
