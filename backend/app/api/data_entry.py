"""Data entry API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlmodel import Session
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
from app.core.security import get_current_user_compat
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["data-entry"])


def get_data_entry_service(session: Session = Depends(get_session)) -> DataEntryService:
    """Dependency to get DataEntryService instance."""
    return DataEntryService(session)


@router.get("/patients", response_model=List[PatientResponse])
async def get_patients(
    user: AuthUser = Depends(get_current_user_compat),
    service: DataEntryService = Depends(get_data_entry_service),
):
    """Get patients visible to the authenticated user (doctor or patient)."""
    try:
        return service.get_all_patients(user)
    except Exception as e:
        logger.error("Error fetching patients: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch patients")


@router.post("/notes/parse", response_model=NotesParseResponse)
async def parse_notes(
    request: NotesParseRequest,
    user: AuthUser = Depends(get_current_user_compat),
    service: DataEntryService = Depends(get_data_entry_service),
):
    """Parse clinical notes using AI (authenticated)."""
    _ = user  # reserved for future per-user rate limits / audit
    try:
        result = await service.parse_clinical_notes(
            notes=request.notes,
            patient_id=request.patient_id,
        )
        return result
    except Exception as e:
        logger.error("Error parsing notes: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to parse clinical notes")


@router.post("/visits", response_model=VisitResponse)
async def create_visit(
    request: CreateVisitRequest,
    user: AuthUser = Depends(get_current_user_compat),
    service: DataEntryService = Depends(get_data_entry_service),
):
    """Create a new visit record for a patient."""
    try:
        result = service.create_visit(request, user)

        if not result.success:
            raise HTTPException(status_code=400, detail=result.message)

        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error creating visit: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create visit")


@router.post("/visits/{visit_id}/ultrasound", response_model=UltrasoundUploadResponse)
async def upload_ultrasound_images(
    visit_id: int,
    files: List[UploadFile] = File(...),
    user: AuthUser = Depends(get_current_user_compat),
    service: DataEntryService = Depends(get_data_entry_service),
):
    """Upload one or more ultrasound images for an existing visit."""
    try:
        uploaded = service.upload_ultrasound_images(visit_id=visit_id, files=files, user=user)
        return UltrasoundUploadResponse(
            success=True,
            message=f"Uploaded {len(uploaded)} ultrasound image(s)",
            uploaded=[UltrasoundImageResponse.model_validate(item) for item in uploaded],
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Error uploading ultrasound images: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to upload ultrasound images")


@router.delete("/ultrasound/{image_id}", response_model=UltrasoundDeleteResponse)
async def delete_ultrasound(
    image_id: int,
    user: AuthUser = Depends(get_current_user_compat),
    service: DataEntryService = Depends(get_data_entry_service),
):
    """Delete an uploaded ultrasound image."""
    try:
        service.delete_ultrasound_image(image_id=image_id, user=user)
        return UltrasoundDeleteResponse(success=True, message="Ultrasound image deleted")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Error deleting ultrasound image: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete ultrasound image")
