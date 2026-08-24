from fastapi import APIRouter

from ncaca.api.v1 import health
from ncaca.api.v1 import ata

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(ata.router)
