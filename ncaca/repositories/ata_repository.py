"""
ncaca/repositories/ata_repository.py
---------------------------------------
The only place ATA touches its data source directly.

Right now this reads from CSV files (mapping.csv, pvalue_by_question.csv),
matching the rest of the current NCACA architecture. If ATA later needs to
read from PostgreSQL instead, ONLY this file changes - the service layer
and optimizer never need to know where the data came from.
"""

import pandas as pd


def load_mapping_and_pvalues(mapping_path: str = "mapping.csv",
                              pvalue_path: str = "pvalue_by_question.csv"):
    """Load the two source tables. Swap this for a DB query later if needed."""
    mapping_df = pd.read_csv(mapping_path)
    pvalue_df = pd.read_csv(pvalue_path)
    return mapping_df, pvalue_df


def load_item_pool(mapping_df: pd.DataFrame, pvalue_df: pd.DataFrame, subject: str) -> pd.DataFrame:
    """Build the full item pool for one subject: every question, its
    competency, and its measured difficulty."""
    pool = mapping_df.merge(
        pvalue_df[["booklet", "qnum", "subject", "p_value", "attempted", "correct"]],
        on=["booklet", "qnum", "subject"],
        how="left",
    )
    return pool[pool["subject"] == subject].copy()
