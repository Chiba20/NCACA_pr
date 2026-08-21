from fastapi import FastAPI

from ncaca.api.v1.router import api_router

app = FastAPI(
    title="NCACA Backend API",
    version="0.1.0",
)

app.include_router(
    api_router,
    prefix="/api/v1",
)