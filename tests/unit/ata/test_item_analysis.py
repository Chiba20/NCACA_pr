import pandas as pd

from ncaca.services.ata.item_analysis import (
    compute_pvalue_by_question,
    attach_competency,
    summarise_by_competency,
    run_item_analysis,
)


def make_sample_data():
    responses = pd.DataFrame(
        {
            "Status": ["scored", "scored", "scored", "pending"],
            "Booklet_Set": [1, 1, 1, 1],
            "Optional_Subject": [
                "Biology",
                "Biology",
                "Biology",
                "Biology",
            ],
            "Q1": [1, 1, 0, 1],
            "Q2": [1, 0, 0, 1],
        }
    )

    mapping = pd.DataFrame(
        {
            "booklet": [1, 1],
            "qnum": [1, 2],
            "subject": ["Mathematics", "Mathematics"],
            "question_id": ["MATH_Q1", "MATH_Q2"],
            "competency_id": ["COMP_A", "COMP_A"],
        }
    )

    return responses, mapping


def test_compute_pvalue_by_question():
    responses, mapping = make_sample_data()

    result = compute_pvalue_by_question(
        responses,
        mapping,
    )

    assert len(result) == 2

    q1 = result[result["qnum"] == 1].iloc[0]
    q2 = result[result["qnum"] == 2].iloc[0]

    assert q1["attempted"] == 3
    assert q1["correct"] == 2
    assert q1["p_value"] == 0.667

    assert q2["attempted"] == 3
    assert q2["correct"] == 1
    assert q2["p_value"] == 0.333


def test_attach_competency():
    responses, mapping = make_sample_data()

    pvalues = compute_pvalue_by_question(
        responses,
        mapping,
    )

    result = attach_competency(
        pvalues,
        mapping,
    )

    assert "question_id" in result.columns
    assert "competency_id" in result.columns

    assert result.iloc[0]["competency_id"] == "COMP_A"


def test_summarise_by_competency():
    responses, mapping = make_sample_data()

    pvalues = compute_pvalue_by_question(
        responses,
        mapping,
    )

    items = attach_competency(
        pvalues,
        mapping,
    )

    result = summarise_by_competency(items)

    assert len(result) == 1
    assert result.iloc[0]["competency_id"] == "COMP_A"
    assert result.iloc[0]["n_items"] == 2
    assert result.iloc[0]["avg_p_value"] == 0.5


def test_run_item_analysis():
    responses, mapping = make_sample_data()

    result = run_item_analysis(
        responses,
        mapping,
    )

    assert "item_pvalues" in result
    assert "competency_summary" in result

    assert len(result["item_pvalues"]) == 2
    assert len(result["competency_summary"]) == 1