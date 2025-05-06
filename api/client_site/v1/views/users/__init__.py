from fastapi import APIRouter
from .email_update import router as email_update_router
from .login import router as login_router
from .profile import router as profile_router
from .register import router as register_router
from .users import router as users_router
from .verification_codes import router as verification_code_router

router = APIRouter()
router.include_router(email_update_router, prefix="/email-update", tags=["Email Update"])
router.include_router(login_router, prefix="/login", tags=["Login"])
router.include_router(profile_router, prefix="/profile", tags=["Profile"])
router.include_router(register_router, prefix="/register", tags=["Register"])
router.include_router(users_router, prefix="/users", tags=["Users"])
router.include_router(verification_code_router, prefix="/verification-codes", tags=["Verification Codes"])