"""
ncaca/tests/unit/ata/test_service.py
----------------------------------------
Tests for the service layer (business orchestration) and API layer,
using small fake mapping/p-value tables - no real CSV files, no real
database, no full-size solve.
"""

import pandas as pd

from ncaca.services.ata import ata_service


def make_fake_mapping():
    return pd.DataFrame({
        "booklet": [1, 1, 2, 2],
        "qnum": [1, 2, 1, 2],
        "subject": ["Mathematics"] * 4,
        "competency_id": ["M-A1", "M-A1", "M-A1", "M-A1"],
        "question_id": ["Q1", "Q2", "Q3", "Q4"],
        "correct_option": ["A", "B", "A", "C"],
    })


def make_fake_pvalues():
    return pd.DataFrame({
        "booklet": [1, 1, 2, 2],
        "qnum": [1, 2, 1, 2],
        "subject": ["Mathematics"] * 4,
        "p_value": [0.8, 0.2, 0.9, 0.1],
        "attempted": [10, 10, 10, 10],
        "correct": [8, 2, 9, 1],
    })


# ---------------------------------------------------------------------
# Service layer tests
# ---------------------------------------------------------------------

def test_get_subjects_summary():
    mapping = make_fake_mapping()
    pvalues = make_fake_pvalues()
    result = ata_service.get_subjects_summary(mapping, pvalues)

    assert result == [{"subject": "Mathematics", "n_competencies": 1, "n_questions": 4}]


def test_get_competency_difficulty():
    mapping = make_fake_mapping()
    pvalues = make_fake_pvalues()
    result = ata_service.get_competency_difficulty(mapping, pvalues, "M-A1")

    assert result["subject"] == "Mathematics"
    assert result["n_questions"] == 4
    assert result["avg_p_value"] == 0.5  # (0.8+0.2+0.9+0.1)/4


def test_get_competency_difficulty_unknown_id():
    mapping = make_fake_mapping()
    pvalues = make_fake_pvalues()
    result = ata_service.get_competency_difficulty(mapping, pvalues, "DOES-NOT-EXIST")

    assert "error" in result


def test_run_ata_optimization_unknown_subject():
    mapping = make_fake_mapping()
    pvalues = make_fake_pvalues()
    result = ata_service.run_ata_optimization(mapping, pvalues, "Not A Real Subject")

    assert "error" in result


def test_run_ata_optimization_returns_balanced_result():
    mapping = make_fake_mapping()
    pvalues = make_fake_pvalues()
    result = ata_service.run_ata_optimization(mapping, pvalues, "Mathematics", time_limit=10)

    assert result["subject"] == "Mathematics"
    assert result["n_items_assigned"] == 4
    assert result["all_hard_rules_passed"] is True
    assert result["spread"] < 0.05
