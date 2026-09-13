"""
ncaca/repositories/ata_repository.py
------------------------------------
ATA data-access boundary.

The current implementation reads local CSV files for development and
verification. File locations can be overridden through environment
variables. A future PostgreSQL implementation can replace this logic
without changing the ATA service or optimizer.
"""

import os
from pathlib import Path

import pandas as pd


DEFAULT_MAPPING_PATH = Path("data") / "ata" / "mapping.csv"
DEFAULT_PVALUE_PATH = Path("data") / "ata" / "outputs" / "pvalue_by_question.csv"


def load_mapping_and_pvalues(
    mapping_path: str | Path | None = None,
    pvalue_path: str | Path | None = None,
):
    """Load ATA mapping and item-difficulty tables."""

    mapping_path = Path(
        mapping_path
        or os.getenv("ATA_MAPPING_PATH", str(DEFAULT_MAPPING_PATH))
    )

    pvalue_path = Path(
        pvalue_path
        or os.getenv("ATA_PVALUE_PATH", str(DEFAULT_PVALUE_PATH))
    )

    mapping_df = pd.read_csv(mapping_path)
    pvalue_df = pd.read_csv(pvalue_path)

    return mapping_df, pvalue_df


def load_item_pool(
    mapping_df: pd.DataFrame,
    pvalue_df: pd.DataFrame,
    subject: str,
) -> pd.DataFrame:
    """Build the item pool for one subject."""

    pool = mapping_df.merge(
        pvalue_df[
            [
                "booklet",
                "qnum",
                "subject",
                "p_value",
                "attempted",
                "correct",
            ]
        ],
        on=["booklet", "qnum", "subject"],
        how="left",
    )

    return pool[pool["subject"] == subject].copy()
