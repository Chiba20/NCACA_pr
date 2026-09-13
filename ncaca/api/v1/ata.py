"""
ncaca/api/v1/ata.py
-------------------
FastAPI routing for ATA.

This layer handles only HTTP concerns and delegates ATA processing to
the service layer or Celery background tasks.
"""

from celery.result import AsyncResult
from fastapi import APIRouter

from ncaca.repositories.ata_repository import load_mapping_and_pvalues
from ncaca.schemas.ata import (
    OptimizeRequest,
    OptimizeTaskResponse,
    OptimizeTaskStatusResponse,
)
from ncaca.services.ata import ata_service
from ncaca.workers.celery_app import celery_app
from ncaca.workers.tasks.ata_tasks import optimize_ata_task


router = APIRouter(
    prefix="/ata",
    tags=["ATA"],
)


@router.get("/subjects")
async def list_subjects():
    """Return available subjects and their ATA item counts."""
    mapping_df, pvalue_df = load_mapping_and_pvalues()

    return ata_service.get_subjects_summary(
        mapping_df,
        pvalue_df,
    )


@router.get("/competencies/{competency_id}")
async def get_competency(competency_id: str):
    """Return difficulty statistics for one competency."""
    mapping_df, pvalue_df = load_mapping_and_pvalues()

    return ata_service.get_competency_difficulty(
        mapping_df,
        pvalue_df,
        competency_id,
    )


@router.post("/optimize", response_model=OptimizeTaskResponse)
async def run_optimizer(request: OptimizeRequest):
    """
    Submit ATA optimization as a Celery background job.
    """
    task = optimize_ata_task.apply_async(
        args=[request.subject, request.time_limit]
    )

    return {
        "task_id": task.id,
        "status": "PENDING",
        "message": "ATA optimization submitted successfully.",
    }


@router.get(
    "/tasks/{task_id}",
    response_model=OptimizeTaskStatusResponse,
)
async def get_optimizer_task_status(task_id: str):
    """
    Check the status and result of an ATA optimization task.
    """
    task = AsyncResult(task_id, app=celery_app)

    if task.successful():
        return {
            "task_id": task_id,
            "status": task.status,
            "result": task.result,
            "error": None,
        }

    if task.failed():
        return {
            "task_id": task_id,
            "status": task.status,
            "result": None,
            "error": str(task.result),
        }

    return {
        "task_id": task_id,
        "status": task.status,
        "result": None,
        "error": None,
    }
