"""
ncaca/services/ata/heuristic.py
--------------------------------
Heuristic ATA booklet balancing.

This module contains the earlier rule-based ATA approach.

For each competency:
1. Sort available items by p-value.
2. Read the required number of items per booklet from the verified design.
3. Distribute items across booklets using a rotating round-robin strategy.
4. Compare booklet difficulty before and after reassignment.

This is the baseline method used before the formal Pyomo + HiGHS optimizer.
"""

import pandas as pd


def required_counts_per_booklet(pool: pd.DataFrame) -> pd.DataFrame:
    """
    Read required item counts per competency and booklet
    from the existing verified booklet design.
    """
    return (
        pool.groupby(["competency_id", "booklet"])
        .size()
        .reset_index(name="required_count")
    )


def assign_by_difficulty(
    pool: pd.DataFrame,
    counts: pd.DataFrame,
) -> pd.DataFrame:
    """
    Assign items using a rule-based difficulty-balancing heuristic.

    Items are sorted by p-value within each competency and distributed
    across booklets while preserving the required competency counts.
    """

    assignments = []

    for comp_index, (competency, comp_items) in enumerate(
        pool.groupby("competency_id")
    ):
        comp_items = (
            comp_items
            .sort_values("p_value")
            .reset_index(drop=True)
        )

        slot_counts = (
            counts[counts["competency_id"] == competency]
            .set_index("booklet")["required_count"]
            .to_dict()
        )

        slots = []

        for booklet, n in sorted(slot_counts.items()):
            slots.extend([booklet] * n)

        if len(slots) != len(comp_items):
            continue

        distinct_booklets = sorted(set(slots))

        offset = comp_index % len(distinct_booklets)

        rotated_booklets = (
            distinct_booklets[offset:]
            + distinct_booklets[:offset]
        )

        remaining = {
            b: slots.count(b)
            for b in distinct_booklets
        }

        booklet_cycle = []

        while sum(remaining.values()) > 0:
            for booklet in rotated_booklets:
                if remaining[booklet] > 0:
                    booklet_cycle.append(booklet)
                    remaining[booklet] -= 1

        for item, new_booklet in zip(
            comp_items.itertuples(),
            booklet_cycle,
        ):
            assignments.append(
                {
                    "competency_id": competency,
                    "question_id": item.question_id,
                    "p_value": item.p_value,
                    "original_booklet": item.booklet,
                    "proposed_booklet": new_booklet,
                }
            )

    return pd.DataFrame(assignments)


def compare_balance(
    pool: pd.DataFrame,
    assignment: pd.DataFrame,
) -> pd.DataFrame:
    """
    Compare average booklet p-values before and after
    heuristic reassignment.
    """

    before = (
        pool.groupby("booklet")["p_value"]
        .mean()
        .round(3)
        .rename("avg_p_before")
    )

    after = (
        assignment.groupby("proposed_booklet")["p_value"]
        .mean()
        .round(3)
        .rename("avg_p_after")
    )

    report = pd.concat(
        [before, after],
        axis=1,
    )

    report.index.name = "booklet"

    report["improvement"] = (
        (report["avg_p_before"] - report["avg_p_before"].mean()).abs().round(3)
        -
        (report["avg_p_after"] - report["avg_p_after"].mean()).abs().round(3)
    )

    return report.reset_index()


def run_heuristic(pool: pd.DataFrame) -> dict:
    """
    Run the complete heuristic ATA stage.
    """

    counts = required_counts_per_booklet(pool)

    assignment = assign_by_difficulty(
        pool,
        counts,
    )

    report = compare_balance(
        pool,
        assignment,
    )

    spread_before = (
        report["avg_p_before"].max()
        - report["avg_p_before"].min()
    )

    spread_after = (
        report["avg_p_after"].max()
        - report["avg_p_after"].min()
    )

    return {
        "assignment": assignment,
        "report": report,
        "spread_before": round(float(spread_before), 4),
        "spread_after": round(float(spread_after), 4),
    }