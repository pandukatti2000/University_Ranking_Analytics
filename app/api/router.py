from fastapi import APIRouter
from app.api.endpoints import health, catalog, analytics, conversations

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(catalog.router, tags=["Catalog & Overview"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
api_router.include_router(conversations.router, prefix="/conversations", tags=["Conversations"])
