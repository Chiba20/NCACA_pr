"""
ncaca/api/v1/ata.py
-----------------------
FastAPI routing for ATA - deliberately thin. This layer only handles
HTTP concerns (routes, request/response shapes) and delegates all real
work to services/ata/ata_service.py. No business logic and no
optimization math should ever live in this file.
"""

from fastapi import APIRouter

from ncaca.repositories.ata_repository import load_mapping_and_pvalues
from ncaca.services.ata import ata_service
from ncaca.schemas.ata import OptimizeRequest, OptimizeResponse

router = APIRouter(
    prefix="/ata",
    tags=["ATA"],
)

# Loaded once at startup - swap for a DB-backed repository call later
# without changing anything below this line.
_mapping_df, _pvalue_df = load_mapping_and_pvalues()


@router.get("/subjects")
async def list_subjects():
    """All subjects, with how many competencies and questions each has."""
    return ata_service.get_subjects_summary(_mapping_df, _pvalue_df)


@router.get("/competencies/{competency_id}")
async def get_competency(competency_id: str):
    """Difficulty stats for one topic - e.g. /api/v1/ata/competencies/M-A1"""
    return ata_service.get_competency_difficulty(_mapping_df, _pvalue_df, competency_id)


@router.post("/optimize", response_model=OptimizeResponse)
async def run_optimizer(request: OptimizeRequest):
    """
    Run the formal Pyomo+HiGHS optimizer for one subject.
    Note: this can take up to `time_limit` seconds (default 60).
    """
    return ata_service.run_ata_optimization(
        _mapping_df, _pvalue_df, request.subject, request.time_limit
    )
