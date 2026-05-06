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
    DoctorOut, RegisteredPatientOut, RegistrationRequestOut
)
from .utils import (
    _require_patient, _require_doctor
)

router = APIRouter()

@router.get("/doctors", response_model=List[DoctorOut])
def list_doctors(session: Session = Depends(get_session)):
    """Return all registered doctors."""
    doctors = session.exec(
        select(AuthUser).where(AuthUser.role == "doctor").where(AuthUser.is_active == True)
    ).all()
    return [DoctorOut(id=d.id, full_name=d.full_name or d.email, email=d.email) for d in doctors]


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
    return DoctorOut(id=doctor.id, full_name=doctor.full_name or doctor.email, email=doctor.email)


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


@router.get("/my-registration-requests", response_model=List[RegistrationRequestOut])
def get_my_registration_requests(
    user: AuthUser = Depends(get_current_user_compat),
    session: Session = Depends(get_session),
):
    """Return the patient's own registration requests."""
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
        result.append(RegistrationRequestOut(
            id=req.id,
            patient_id=req.patient_id,
            patient_name=doctor_user.full_name or doctor_user.email if doctor_user else "Unknown",
            patient_email=doctor_user.email if doctor_user else "",
            doctor_id=req.doctor_id,
            appointment_id=req.appointment_id,
            appointment_date=appt.appointment_date if appt else None,
            appointment_start_time=appt.start_time if appt else None,
            status=req.status,
            created_at=req.created_at,
        ))
    return result
