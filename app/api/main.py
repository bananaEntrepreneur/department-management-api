from fastapi import APIRouter

from app.api.routes.department import departments_router

api_router = APIRouter()

api_router.include_router(departments_router)


@api_router.get("/")
async def health_check():
    return {"status": "healty"}
