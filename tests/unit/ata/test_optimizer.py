"""
ncaca/tests/unit/ata/test_optimizer.py
------------------------------------------
Unit tests for the isolated optimizer - no API, no database, no service
layer involved. Uses small hand-verified fake data.
"""

import pandas as pd
import pytest

from ncaca.services.ata.optimizer import (
    required_counts, build_model, solve, extract_assignment, validate, run_optimizer,
)


def make_fake_pool():
    """4 items, 1 competency, 2 booklets, 2 items each."""
    return pd.DataFrame({
        "booklet": [1, 1, 2, 2],
        "question_id": ["Q1", "Q2", "Q3", "Q4"],
        "competency_id": ["M-A1", "M-A1", "M-A1", "M-A1"],
        "p_value": [0.8, 0.2, 0.9, 0.1],
    })


def test_required_counts_reads_existing_design():
    pool = make_fake_pool()
    counts = required_counts(pool)
    assert counts[("M-A1", 1)] == 2
    assert counts[("M-A1", 2)] == 2


def test_optimizer_satisfies_both_hard_constraints():
    pool = make_fake_pool()
    model = build_model(pool)
    status, elapsed = solve(model, time_limit=10)
    assignment = extract_assignment(model, pool)
    report = validate(assignment, pool)

    assert report["all_hard_rules_passed"] is True
    for check in report["checks"]:
        assert check["passed"] is True


def test_optimizer_minimizes_difficulty_gap():
    pool = make_fake_pool()
    model = build_model(pool)
    solve(model, time_limit=10)
    assignment = extract_assignment(model, pool)

    avg_by_booklet = assignment.groupby("optimized_booklet")["p_value"].mean()
    spread = avg_by_booklet.max() - avg_by_booklet.min()
    assert spread < 0.05


def test_run_optimizer_entry_point_returns_expected_keys():
    """The single public entry point should return everything the
    service layer needs, in one call."""
    pool = make_fake_pool()
    result = run_optimizer(pool, time_limit=10)

    assert "assignment" in result
    assert "report" in result
    assert "spread" in result
    assert result["report"]["all_hard_rules_passed"] is True
