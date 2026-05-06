from fastapi import APIRouter
from .availability import router as availability_router
from .booking import router as booking_router
from .registration import router as registration_router
from .notifications import router as notifications_router

router = APIRouter(prefix="/appointments", tags=["Appointments"])

router.include_router(availability_router)
router.include_router(booking_router)
router.include_router(registration_router)
router.include_router(notifications_router)
