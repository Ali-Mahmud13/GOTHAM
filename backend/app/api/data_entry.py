"""Data entry API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from typing import List

from app.db.session import get_session
from app.schemas import (
    PatientResponse,
    NotesParseRequest,
    NotesParseResponse,
    CreateVisitRequest,
    VisitResponse,
)
from app.services.data_entry_service import DataEntryService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["data-entry"])


def get_data_entry_service(session: Session = Depends(get_session)) -> DataEntryService:
    """Dependency to get DataEntryService instance."""
    return DataEntryService(session)


@router.get("/patients", response_model=List[PatientResponse])
async def get_patients(
    service: DataEntryService = Depends(get_data_entry_service)
):
    """
    Get all patients with their latest visit information.
    
    Returns:
        List of patients with metadata
    """
    try:
        patients = service.get_all_patients()
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
        result = service.create_visit(request)
        
        if not result.success:
            raise HTTPException(status_code=400, detail=result.message)
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating visit: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create visit")
