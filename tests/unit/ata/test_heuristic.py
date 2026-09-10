import pandas as pd

from ncaca.services.ata.heuristic import (
    required_counts_per_booklet,
    assign_by_difficulty,
    compare_balance,
    run_heuristic,
)


def make_sample_pool():
    return pd.DataFrame(
        {
            "booklet": [1, 1, 2, 2, 1, 1, 2, 2],
            "question_id": [
                "Q1", "Q2", "Q3", "Q4",
                "Q5", "Q6", "Q7", "Q8",
            ],
            "competency_id": [
                "C1", "C1", "C1", "C1",
                "C2", "C2", "C2", "C2",
            ],
            "p_value": [
                0.2, 0.8, 0.3, 0.7,
                0.1, 0.9, 0.4, 0.6,
            ],
        }
    )


def test_required_counts_per_booklet():
    pool = make_sample_pool()

    result = required_counts_per_booklet(pool)

    assert len(result) == 4

    c1_b1 = result[
        (result["competency_id"] == "C1")
        & (result["booklet"] == 1)
    ].iloc[0]

    assert c1_b1["required_count"] == 2


def test_assign_by_difficulty_preserves_all_items():
    pool = make_sample_pool()

    counts = required_counts_per_booklet(pool)

    result = assign_by_difficulty(
        pool,
        counts,
    )

    assert len(result) == len(pool)
    assert result["question_id"].nunique() == len(pool)


def test_assign_by_difficulty_preserves_competency_counts():
    pool = make_sample_pool()

    counts = required_counts_per_booklet(pool)

    assignment = assign_by_difficulty(
        pool,
        counts,
    )

    assigned_counts = (
        assignment.groupby(
            ["competency_id", "proposed_booklet"]
        )
        .size()
        .reset_index(name="assigned_count")
    )

    merged = counts.merge(
        assigned_counts,
        left_on=["competency_id", "booklet"],
        right_on=["competency_id", "proposed_booklet"],
    )

    assert (
        merged["required_count"]
        == merged["assigned_count"]
    ).all()


def test_compare_balance_returns_before_and_after():
    pool = make_sample_pool()

    counts = required_counts_per_booklet(pool)

    assignment = assign_by_difficulty(
        pool,
        counts,
    )

    report = compare_balance(
        pool,
        assignment,
    )

    assert "avg_p_before" in report.columns
    assert "avg_p_after" in report.columns
    assert "improvement" in report.columns


def test_run_heuristic_returns_expected_result():
    pool = make_sample_pool()

    result = run_heuristic(pool)

    assert "assignment" in result
    assert "report" in result
    assert "spread_before" in result
    assert "spread_after" in result

    assert len(result["assignment"]) == len(pool)