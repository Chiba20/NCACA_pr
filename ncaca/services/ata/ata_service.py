"""
ncaca/services/ata/ata_service.py
------------------------------------
Business orchestration for ATA.

This layer decides WHAT to do and in WHAT order - it does not do the
optimization math itself (that's optimizer.py), and it does not know
about HTTP requests or responses (that's api/v1/ata.py). If ATA later
needs real database access instead of CSV files, only the data-loading
functions here change - the API layer and the optimizer stay untouched.
"""

import pandas as pd

from ncaca.services.ata.optimizer import run_optimizer
from ncaca.repositories.ata_repository import load_item_pool


def get_subjects_summary(mapping_df: pd.DataFrame, pvalue_df: pd.DataFrame) -> list[dict]:
    """List every subject with its competency and question counts."""
    items = _build_items(mapping_df, pvalue_df)
    result = []
    for subject in sorted(items["subject"].unique()):
        subset = items[items["subject"] == subject]
        result.append({
            "subject": subject,
            "n_competencies": int(subset["competency_id"].nunique()),
            "n_questions": int(len(subset)),
        })
    return result


def get_competency_difficulty(mapping_df: pd.DataFrame, pvalue_df: pd.DataFrame,
                               competency_id: str) -> dict:
    """Difficulty stats for one competency."""
    items = _build_items(mapping_df, pvalue_df)
    subset = items[items["competency_id"] == competency_id]

    if len(subset) == 0:
        return {"error": f"No competency found with id '{competency_id}'"}

    p_values = subset["p_value"].dropna()
    return {
        "competency_id": competency_id,
        "subject": subset["subject"].iloc[0],
        "n_questions": int(len(subset)),
        "avg_p_value": round(float(p_values.mean()), 3) if len(p_values) else None,
        "hardest_p_value": round(float(p_values.min()), 3) if len(p_values) else None,
        "easiest_p_value": round(float(p_values.max()), 3) if len(p_values) else None,
    }


def run_ata_optimization(mapping_df: pd.DataFrame, pvalue_df: pd.DataFrame,
                          subject: str, time_limit: int = 60) -> dict:
    """
    The main ATA task: given a subject, run the formal optimizer and
    return a validated, balanced booklet assignment.
    """
    pool = load_item_pool(mapping_df, pvalue_df, subject)

    if len(pool) == 0:
        return {"error": f"No subject found called '{subject}'"}

    result = run_optimizer(pool, time_limit=time_limit)

    return {
        "subject": subject,
        "n_items_assigned": int(len(result["assignment"])),
        "avg_difficulty_per_booklet": result["report"]["avg_difficulty_per_booklet"],
        "spread": result["spread"],
        "solver_status": result["report"]["solver_status"],
        "all_hard_rules_passed": result["report"]["all_hard_rules_passed"],
    }


def _build_items(mapping_df: pd.DataFrame, pvalue_df: pd.DataFrame) -> pd.DataFrame:
    """Join mapping and p-value data into one item table."""
    return mapping_df.merge(
        pvalue_df[["booklet", "qnum", "subject", "p_value", "attempted", "correct"]],
        on=["booklet", "qnum", "subject"],
        how="left",
    )
