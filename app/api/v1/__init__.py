from fastapi import APIRouter
from app.api.v1.wallets import router as wallets_router
from app.api.v1.jobs import router as jobs_router
from app.api.v1.tokens import router as tokens_router

api_router = APIRouter()
api_router.include_router(tokens_router)
api_router.include_router(jobs_router)
api_router.include_router(wallets_router)