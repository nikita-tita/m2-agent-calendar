"""
API v1 роутер
"""
from fastapi import APIRouter

# from app.api.v1.endpoints import properties, calendar, analytics, auth, miniapp
from app.api.v1.endpoints import analytics, auth, miniapp

api_router = APIRouter()

# api_router.include_router(properties.router, prefix="/properties", tags=["properties"])
# api_router.include_router(calendar.router, prefix="/calendar", tags=["calendar"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(miniapp.router, prefix="/miniapp", tags=["miniapp"])

# Placeholder endpoints - will be implemented when endpoint modules are created
@api_router.get("/")
async def api_root():
    """API root endpoint"""
    return {"message": "RealEstate Calendar Bot API v1"} 