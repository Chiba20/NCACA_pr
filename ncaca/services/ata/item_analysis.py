"""
ncaca/services/ata/item_analysis.py
-----------------------------------
Item analysis for Automated Test Assembly (ATA).

This module converts scored student responses into item-level
difficulty statistics.

Expected scored response values:
    1 = correct
    0 = incorrect
    NaN = not attempted / not applicable

Main statistic:
    p-value = number_correct / number_attempted

Higher p-value -> relatively easier item
Lower p-value  -> relatively harder item
"""

import pandas as pd


def compute_pvalue_by_question(
    responses: pd.DataFrame,
    mapping: pd.DataFrame,
) -> pd.DataFrame:
    """
    Compute item p-values for every booklet/question combination.

    Only responses with Status == "scored" are used.

    Biology and Computer Studies share positions 49-60, so students
    are filtered using Optional_Subject before calculating statistics.
    """

    responses = responses[responses["Status"] == "scored"].copy()

    results = []

    for booklet_set, group in responses.groupby("Booklet_Set"):

        booklet_set = int(booklet_set)

        booklet_map = mapping[
            mapping["booklet"] == booklet_set
        ]

        for qnum in range(1, 61):

            column = f"Q{qnum}"

            if column not in responses.columns:
                continue

            subjects_here = booklet_map.loc[
                booklet_map["qnum"] == qnum,
                "subject"
            ].unique()

            for subject in subjects_here:

                if subject in ("Biology", "Computer Studies"):
                    subset = group[
                        group["Optional_Subject"] == subject
                    ]
                else:
                    subset = group

                attempted = subset[column].notna().sum()
                correct = subset[column].sum()

                if attempted == 0:
                    continue

                results.append(
                    {
                        "booklet": booklet_set,
                        "qnum": qnum,
                        "subject": subject,
                        "attempted": int(attempted),
                        "correct": int(correct),
                        "p_value": round(
                            float(correct / attempted),
                            3,
                        ),
                    }
                )

    return pd.DataFrame(results)


def attach_competency(
    pvalue_df: pd.DataFrame,
    mapping: pd.DataFrame,
) -> pd.DataFrame:
    """
    Attach question_id and competency_id to calculated p-values.
    """

    return pvalue_df.merge(
        mapping[
            [
                "booklet",
                "qnum",
                "subject",
                "question_id",
                "competency_id",
            ]
        ],
        on=["booklet", "qnum", "subject"],
        how="left",
    )


def summarise_by_competency(
    item_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Calculate average p-value for each competency.
    """

    return (
        item_df.groupby("competency_id")["p_value"]
        .agg(
            avg_p_value="mean",
            n_items="count",
        )
        .round(3)
        .sort_values("avg_p_value")
        .reset_index()
    )


def run_item_analysis(
    responses_df: pd.DataFrame,
    mapping_df: pd.DataFrame,
) -> dict:
    """
    Run the complete ATA item-analysis stage.

    Returns:
        item_pvalues:
            question-level p-values with competency information

        competency_summary:
            average p-value by competency
    """

    pvalues = compute_pvalue_by_question(
        responses_df,
        mapping_df,
    )

    items = attach_competency(
        pvalues,
        mapping_df,
    )

    competency_summary = summarise_by_competency(items)

    return {
        "item_pvalues": items,
        "competency_summary": competency_summary,
    }