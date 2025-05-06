from fastapi import APIRouter
from .email_update import router as email_update_router
from .login import router as login_router
from .profile import router as profile_router
from .register import router as register_router
from .users import router as users_router
from .verification_codes import router as verification_code_router

router = APIRouter()
router.include_router(email_update_router, tags=["Email Update"])
router.include_router(login_router, tags=["Login"])
router.include_router(profile_router, tags=["Profile"])
router.include_router(register_router, tags=["Register"])
router.include_router(users_router, tags=["Users"])
router.include_router(verification_code_router, tags=["Verification Codes"])