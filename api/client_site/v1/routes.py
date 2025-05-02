from fastapi import APIRouter
from .views import users, tariffs, notifications, tests, transactions, analyses

router = APIRouter()

router.include_router(users.router, prefix="/users", tags=["Users"])
router.include_router(tariffs.router, prefix="/tariffs", tags=["Tariffs"])
router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
router.include_router(tests.listening.router, prefix="/tests/listening", tags=["Listening Tests"])
router.include_router(tests.reading.router, prefix="/tests/reading", tags=["Reading Tests"])
router.include_router(tests.writing.router, prefix="/tests/writing", tags=["Writing Tests"])
router.include_router(tests.speaking.router, prefix="/tests/speaking", tags=["Speaking Tests"])
router.include_router(tests.grammar.router, prefix="/tests/grammar", tags=["Grammar Tests"])
router.include_router(transactions.router, prefix="/transactions", tags=["Transactions"])
router.include_router(analyses.router, prefix="/analyses", tags=["Analyses"])