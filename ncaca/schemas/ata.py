"""
ncaca/schemas/ata.py
------------------------
Defines the shape of data going in and out of the ATA API - using
Pydantic so FastAPI can validate requests automatically and generate
accurate documentation.
"""

from pydantic import BaseModel


class SubjectSummary(BaseModel):
    subject: str
    n_competencies: int
    n_questions: int


class CompetencyDifficulty(BaseModel):
    competency_id: str
    subject: str
    n_questions: int
    avg_p_value: float | None
    hardest_p_value: float | None
    easiest_p_value: float | None


class OptimizeRequest(BaseModel):
    subject: str
    time_limit: int = 60


class OptimizeResponse(BaseModel):
    subject: str
    n_items_assigned: int
    avg_difficulty_per_booklet: dict[int, float]
    spread: float
    solver_status: str
    all_hard_rules_passed: bool


class ErrorResponse(BaseModel):
    error: str
