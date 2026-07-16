from fastapi import APIRouter
from app.api.v1.wallets import router as wallets_router, whale_events_router
from app.api.v1.jobs import router as jobs_router
from app.api.v1.tokens import router as tokens_router
from app.api.v1.contract_security import router as scan
from app.api.v1.social import router as social_router
from app.api.v1.narratives import router as narrative_router


api_router = APIRouter()
api_router.include_router(tokens_router)
api_router.include_router(jobs_router)
api_router.include_router(wallets_router)
api_router.include_router(scan)
api_router.include_router(whale_events_router)
api_router.include_router(social_router)
api_router.include_router(narrative_router)