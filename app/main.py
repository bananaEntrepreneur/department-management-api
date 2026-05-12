import uvicorn
from fastapi import FastAPI

from app.api.main import api_router
from app.admin import setup_admin

app = FastAPI(title="API for department management")
app.include_router(api_router)
setup_admin(app)


if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True
    )
