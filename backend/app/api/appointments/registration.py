from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError

from app.db.session import get_session
from app.core.security import get_current_user_compat
from app.models.auth import AuthUser
from app.models.appointments import Appointment, RegistrationRequest
from app.models.patient import Patient, Visit

from .schemas import (
    DoctorOut, RegisteredPatientOut, RegistrationRequestOut,
    PatientRegistrationRequestOut, StandaloneRegistrationRequest
)
from .utils import (
    _require_patient, _require_doctor
)

router = APIRouter()

@router.get("/doctors", response_model=List[DoctorOut])
def list_doctors(session: Session = Depends(get_session)):
    """Return all registered, verified doctors."""
    doctors = session.exec(
        select(AuthUser)
        .where(AuthUser.role == "doctor")
        .where(AuthUser.is_active == True)
        .where(AuthUser.verification_status == "verified")
    ).all()
    return [
        DoctorOut(
            id=d.id,
            full_name=d.full_name or d.email,
            email=d.email,
            specialty=d.specialty,
            clinic_name=d.clinic_name,
            bio=d.bio,
        )
        for d in doctors
    ]


@router.get("/my-doctor", response_model=Optional[DoctorOut])
def get_my_doctor(
    user: AuthUser = Depends(get_current_user_compat),
    session: Session = Depends(get_session),
):
    """Return the patient's currently registered doctor."""
    _require_patient(user)
    patient = session.get(Patient, user.patient_id) if user.patient_id else None
    if not patient or not patient.doctor_id:
        return None
    doctor = session.get(AuthUser, patient.doctor_id)
    if not doctor or doctor.role != "doctor":
        return None
    return DoctorOut(
        id=doctor.id,
        full_name=doctor.full_name or doctor.email,
        email=doctor.email,
        specialty=doctor.specialty,
        clinic_name=doctor.clinic_name,
        bio=doctor.bio,
    )


@router.delete("/unregister", status_code=200)
def patient_unregister(
    user: AuthUser = Depends(get_current_user_compat),
    session: Session = Depends(get_session),
):
    """Patient unregisters themselves."""
    _require_patient(user)
    patient = session.get(Patient, user.patient_id) if user.patient_id else None
    if not patient or not patient.doctor_id:
        raise HTTPException(status_code=400, detail="Not registered.")

    patient.doctor_id = None
    patient.clinical_notes = None
    session.add(patient)
    session.commit()
    return {"detail": "Successfully unregistered"}


@router.post("/register", response_model=RegistrationRequestOut, status_code=201)
def standalone_register_with_doctor(
    body: StandaloneRegistrationRequest,
    user: AuthUser = Depends(get_current_user_compat),
    session: Session = Depends(get_session),
):
    """Patient sends a standalone registration request to a doctor (no appointment required)."""
    _require_patient(user)

    # Check doctor exists and is verified
    doctor = session.get(AuthUser, body.doctor_id)
    if not doctor or doctor.role != "doctor" or not doctor.is_active:
        raise HTTPException(status_code=404, detail="Doctor not found.")

    # Prevent duplicate pending requests
    existing = session.exec(
        select(RegistrationRequest)
        .where(RegistrationRequest.patient_id == user.id)
        .where(RegistrationRequest.doctor_id == body.doctor_id)
        .where(RegistrationRequest.status == "pending")
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="You already have a pending registration request with this doctor.")

    # Check if already registered with this or another doctor
    patient = session.get(Patient, user.patient_id) if user.patient_id else None
    if patient and patient.doctor_id:
        if patient.doctor_id == body.doctor_id:
            raise HTTPException(status_code=400, detail="You are already registered with this doctor.")
        raise HTTPException(
            status_code=400,
            detail="You are already registered with another doctor. Please unregister first.",
        )

    reg_request = RegistrationRequest(
        patient_id=user.id,
        doctor_id=body.doctor_id,
        appointment_id=None,
        status="pending",
    )
    session.add(reg_request)
    session.commit()
    session.refresh(reg_request)

    return RegistrationRequestOut(
        id=reg_request.id,
        patient_id=reg_request.patient_id,
        patient_name=user.full_name or user.email,
        patient_email=user.email,
        doctor_id=reg_request.doctor_id,
        appointment_id=None,
        appointment_date=None,
        appointment_start_time=None,
        status=reg_request.status,
        created_at=reg_request.created_at,
    )


@router.get("/my-registered-patients", response_model=List[RegisteredPatientOut])
def get_my_registered_patients(
    user: AuthUser = Depends(get_current_user_compat),
    session: Session = Depends(get_session),
):
    """Return all patients registered under this doctor."""
    _require_doctor(user)
    patients = session.exec(
        select(Patient).where(Patient.doctor_id == user.id).order_by(Patient.name)
    ).all()
    result = []
    for p in patients:
        auth_user = session.exec(select(AuthUser).where(AuthUser.patient_id == p.id)).first()
        result.append(RegisteredPatientOut(
            patient_auth_id=auth_user.id if auth_user else 0,
            patient_name=p.name,
            patient_email=auth_user.email if auth_user else "",
            patient_identifier=p.patient_identifier,
        ))
    return result


@router.get("/registration-requests", response_model=List[RegistrationRequestOut])
def get_registration_requests(
    user: AuthUser = Depends(get_current_user_compat),
    session: Session = Depends(get_session),
):
    """Return pending registration requests."""
    _require_doctor(user)
    requests = session.exec(
        select(RegistrationRequest)
        .where(RegistrationRequest.doctor_id == user.id)
        .where(RegistrationRequest.status == "pending")
        .order_by(RegistrationRequest.created_at.desc())
    ).all()
    result = []
    for req in requests:
        patient_user = session.get(AuthUser, req.patient_id)
        appt = session.get(Appointment, req.appointment_id) if req.appointment_id else None
        result.append(RegistrationRequestOut(
            id=req.id,
            patient_id=req.patient_id,
            patient_name=patient_user.full_name if patient_user else "Unknown",
            patient_email=patient_user.email if patient_user else "",
            doctor_id=req.doctor_id,
            appointment_id=req.appointment_id,
            appointment_date=appt.appointment_date if appt else None,
            appointment_start_time=appt.start_time if appt else None,
            status=req.status,
            created_at=req.created_at,
        ))
    return result


@router.put("/registration-requests/{request_id}/approve", response_model=RegistrationRequestOut)
def approve_registration_request(
    request_id: int,
    user: AuthUser = Depends(get_current_user_compat),
    session: Session = Depends(get_session),
):
    """Approve a registration request."""
    _require_doctor(user)
    reg_req = session.get(RegistrationRequest, request_id)
    if not reg_req or reg_req.doctor_id != user.id:
        raise HTTPException(status_code=404, detail="Request not found")
    if reg_req.status != "pending":
        raise HTTPException(status_code=400, detail="Already processed")

    # Update patient record
    patient_auth = session.get(AuthUser, reg_req.patient_id)
    if patient_auth and patient_auth.patient_id:
        p = session.get(Patient, patient_auth.patient_id)
        if p:
            p.doctor_id = user.id
            session.add(p)

    # Approve appt
    if reg_req.appointment_id:
        appt = session.get(Appointment, reg_req.appointment_id)
        if appt and appt.status == "pending_approval":
            appt.status = "booked"
            session.add(appt)

    reg_req.status = "approved"
    reg_req.updated_at = datetime.utcnow()
    session.add(reg_req)
    session.commit()
    session.refresh(reg_req)
    
    patient_user = session.get(AuthUser, reg_req.patient_id)
    appt = session.get(Appointment, reg_req.appointment_id) if reg_req.appointment_id else None
    return RegistrationRequestOut(
        id=reg_req.id,
        patient_id=reg_req.patient_id,
        patient_name=patient_user.full_name if patient_user else "Unknown",
        patient_email=patient_user.email if patient_user else "",
        doctor_id=reg_req.doctor_id,
        appointment_id=reg_req.appointment_id,
        appointment_date=appt.appointment_date if appt else None,
        appointment_start_time=appt.start_time if appt else None,
        status=reg_req.status,
        created_at=reg_req.created_at,
    )


@router.put("/registration-requests/{request_id}/decline", response_model=RegistrationRequestOut)
def decline_registration_request(
    request_id: int,
    user: AuthUser = Depends(get_current_user_compat),
    session: Session = Depends(get_session),
):
    """Decline a registration request."""
    _require_doctor(user)
    reg_req = session.get(RegistrationRequest, request_id)
    if not reg_req or reg_req.doctor_id != user.id:
        raise HTTPException(status_code=404, detail="Request not found")
    
    if reg_req.appointment_id:
        appt = session.get(Appointment, reg_req.appointment_id)
        if appt and appt.status == "pending_approval":
            appt.status = "cancelled"
            session.add(appt)

    reg_req.status = "declined"
    reg_req.updated_at = datetime.utcnow()
    session.add(reg_req)
    session.commit()
    session.refresh(reg_req)

    patient_user = session.get(AuthUser, reg_req.patient_id)
    appt = session.get(Appointment, reg_req.appointment_id) if reg_req.appointment_id else None
    return RegistrationRequestOut(
        id=reg_req.id,
        patient_id=reg_req.patient_id,
        patient_name=patient_user.full_name if patient_user else "Unknown",
        patient_email=patient_user.email if patient_user else "",
        doctor_id=reg_req.doctor_id,
        appointment_id=reg_req.appointment_id,
        appointment_date=appt.appointment_date if appt else None,
        appointment_start_time=appt.start_time if appt else None,
        status=reg_req.status,
        created_at=reg_req.created_at,
    )


@router.get("/my-registration-requests", response_model=List[PatientRegistrationRequestOut])
def get_my_registration_requests(
    user: AuthUser = Depends(get_current_user_compat),
    session: Session = Depends(get_session),
):
    """Return the patient's own registration requests (shows doctor info)."""
    _require_patient(user)
    reqs = session.exec(
        select(RegistrationRequest)
        .where(RegistrationRequest.patient_id == user.id)
        .order_by(RegistrationRequest.updated_at.desc())
    ).all()
    result = []
    for req in reqs:
        doctor_user = session.get(AuthUser, req.doctor_id)
        appt = session.get(Appointment, req.appointment_id) if req.appointment_id else None
        result.append(PatientRegistrationRequestOut(
            id=req.id,
            patient_id=req.patient_id,
            doctor_id=req.doctor_id,
            doctor_name=doctor_user.full_name or doctor_user.email if doctor_user else "Unknown",
            doctor_email=doctor_user.email if doctor_user else "",
            appointment_id=req.appointment_id,
            appointment_date=appt.appointment_date if appt else None,
            appointment_start_time=appt.start_time if appt else None,
            status=req.status,
            created_at=req.created_at,
        ))
    return result
