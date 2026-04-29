"""Data entry API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Header, UploadFile, File
from sqlmodel import Session, select
from typing import List

from app.db.session import get_session
from app.schemas import (
    PatientResponse,
    NotesParseRequest,
    NotesParseResponse,
    CreateVisitRequest,
    VisitResponse,
    UltrasoundUploadResponse,
    UltrasoundDeleteResponse,
    UltrasoundImageResponse,
)
from app.services.data_entry_service import DataEntryService
from app.models.auth import AuthUser
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["data-entry"])


def get_data_entry_service(session: Session = Depends(get_session)) -> DataEntryService:
    """Dependency to get DataEntryService instance."""
    return DataEntryService(session)


def get_request_user(
    user_email: str | None,
    session: Session,
) -> AuthUser | None:
    """Resolve authenticated user from X-User-Email header, when provided."""
    if not user_email:
        return None
    return session.exec(select(AuthUser).where(AuthUser.email == user_email.lower())).first()


@router.get("/patients", response_model=List[PatientResponse])
async def get_patients(
    user_email: str | None = Header(None, alias="X-User-Email"),
    service: DataEntryService = Depends(get_data_entry_service)
):
    """
    Get all patients with their latest visit information.
    
    Returns:
        List of patients with metadata
    """
    try:
        user = get_request_user(user_email, service.session)
        patients = service.get_all_patients(user)
        return patients
    except Exception as e:
        logger.error(f"Error fetching patients: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch patients")


@router.post("/notes/parse", response_model=NotesParseResponse)
async def parse_notes(
    request: NotesParseRequest,
    service: DataEntryService = Depends(get_data_entry_service)
):
    """
    Parse clinical notes using AI to extract structured data.
    
    Args:
        request: NotesParseRequest with clinical notes text
        
    Returns:
        Extracted fields and missing required fields
    """
    try:
        result = await service.parse_clinical_notes(
            notes=request.notes,
            patient_id=request.patient_id
        )
        return result
    except Exception as e:
        logger.error(f"Error parsing notes: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to parse clinical notes")


@router.post("/visits", response_model=VisitResponse)
async def create_visit(
    request: CreateVisitRequest,
    user_email: str | None = Header(None, alias="X-User-Email"),
    service: DataEntryService = Depends(get_data_entry_service)
):
    """
    Create a new visit record for a patient.
    
    Args:
        request: CreateVisitRequest with visit data
        
    Returns:
        Visit creation result with visit ID
    """
    try:
        user = get_request_user(user_email, service.session)
        result = service.create_visit(request, user)
        
        if not result.success:
            raise HTTPException(status_code=400, detail=result.message)
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating visit: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create visit")


@router.post("/visits/{visit_id}/ultrasound", response_model=UltrasoundUploadResponse)
async def upload_ultrasound_images(
    visit_id: int,
    files: List[UploadFile] = File(...),
    user_email: str | None = Header(None, alias="X-User-Email"),
    service: DataEntryService = Depends(get_data_entry_service),
):
    """Upload one or more ultrasound images for an existing visit."""
    try:
        user = get_request_user(user_email, service.session)
        uploaded = service.upload_ultrasound_images(visit_id=visit_id, files=files, user=user)
        return UltrasoundUploadResponse(
            success=True,
            message=f"Uploaded {len(uploaded)} ultrasound image(s)",
            uploaded=[UltrasoundImageResponse.model_validate(item) for item in uploaded],
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error uploading ultrasound images: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to upload ultrasound images")


@router.delete("/ultrasound/{image_id}", response_model=UltrasoundDeleteResponse)
async def delete_ultrasound(
    image_id: int,
    user_email: str | None = Header(None, alias="X-User-Email"),
    service: DataEntryService = Depends(get_data_entry_service),
):
    """Delete an uploaded ultrasound image."""
    try:
        user = get_request_user(user_email, service.session)
        service.delete_ultrasound_image(image_id=image_id, user=user)
        return UltrasoundDeleteResponse(success=True, message="Ultrasound image deleted")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting ultrasound image: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete ultrasound image")
