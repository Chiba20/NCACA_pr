"""
ncaca/services/ata/optimizer.py
---------------------------------
The ATA optimization algorithm, isolated from everything else.

This module ONLY knows about the math: given an item pool (questions with
their difficulty and competency), build and solve the block-assignment
model. It does not know about the API, HTTP, or the database - it just
takes data in and returns a result.

This isolation is deliberate: the optimizer can be unit tested completely
on its own, with no API or database involved.
"""

import time
import pandas as pd
import pyomo.environ as pyo


def required_counts(pool: pd.DataFrame) -> dict:
    """
    Required item count per (competency, booklet), read directly from the
    already-verified design in the item pool - not invented here.
    """
    return pool.groupby(["competency_id", "booklet"]).size().to_dict()


def build_model(pool: pd.DataFrame):
    """
    Build the MILP model.

    Decision variable:
        x[i, b] = 1 if item i is assigned to booklet b, else 0

    Hard constraints:
        H1 - every item assigned to exactly one booklet
        H2 - topic coverage per booklet matches the verified design exactly

    Objective (soft):
        minimize (hardest booklet's total difficulty - easiest booklet's)
    """
    items = pool["question_id"].tolist()
    p = dict(zip(pool["question_id"], pool["p_value"]))
    comp = dict(zip(pool["question_id"], pool["competency_id"]))
    booklets = sorted(pool["booklet"].unique().tolist())
    competencies = sorted(pool["competency_id"].unique().tolist())
    req = required_counts(pool)

    model = pyo.ConcreteModel(name="ATA_Block_Assignment")
    model.I = pyo.Set(initialize=items)
    model.B = pyo.Set(initialize=booklets)
    model.C = pyo.Set(initialize=competencies)
    model.x = pyo.Var(model.I, model.B, domain=pyo.Binary)

    def one_booklet_rule(mdl, i):
        return sum(mdl.x[i, b] for b in mdl.B) == 1
    model.H1_one_booklet = pyo.Constraint(model.I, rule=one_booklet_rule)

    items_by_comp = {c: [i for i in items if comp[i] == c] for c in competencies}

    def coverage_rule(mdl, c, b):
        required = req.get((c, b), 0)
        return sum(mdl.x[i, b] for i in items_by_comp[c]) == required
    model.H2_coverage = pyo.Constraint(model.C, model.B, rule=coverage_rule)

    model.booklet_p = pyo.Var(model.B, domain=pyo.NonNegativeReals)

    def booklet_p_rule(mdl, b):
        return mdl.booklet_p[b] == sum(p[i] * mdl.x[i, b] for i in mdl.I)
    model.booklet_p_con = pyo.Constraint(model.B, rule=booklet_p_rule)

    model.maxP = pyo.Var(domain=pyo.NonNegativeReals)
    model.minP = pyo.Var(domain=pyo.NonNegativeReals)
    model.max_con = pyo.Constraint(model.B, rule=lambda mdl, b: mdl.maxP >= mdl.booklet_p[b])
    model.min_con = pyo.Constraint(model.B, rule=lambda mdl, b: mdl.minP <= mdl.booklet_p[b])
    model.obj = pyo.Objective(expr=model.maxP - model.minP, sense=pyo.minimize)

    return model


def solve(model, time_limit: int = 60, mip_gap: float = 0.02):
    """
    Solve using Pyomo's 'highs' interface (not 'appsi_highs' - that
    interface was found to ignore the configured time limit and hang
    indefinitely on problems this size, due to symmetry between
    interchangeable items).
    """
    solver = pyo.SolverFactory("highs")
    start = time.time()
    results = solver.solve(model, options={"time_limit": time_limit, "mip_rel_gap": mip_gap})
    elapsed = round(time.time() - start, 2)
    status = str(results.solver.termination_condition)
    return status, elapsed


def extract_assignment(model, pool: pd.DataFrame) -> pd.DataFrame:
    """Turn the solved model's variables back into a plain DataFrame."""
    rows = []
    for i in model.I:
        for b in model.B:
            if pyo.value(model.x[i, b]) > 0.5:
                rows.append({"question_id": i, "optimized_booklet": b})
    assignment = pd.DataFrame(rows)
    return assignment.merge(
        pool[["question_id", "competency_id", "p_value", "booklet"]].rename(
            columns={"booklet": "original_booklet"}),
        on="question_id", how="left",
    )


def validate(assignment: pd.DataFrame, pool: pd.DataFrame) -> dict:
    """
    Independently re-check every hard rule against the solved assignment -
    do not just trust the solver's own success message.
    """
    report = {"checks": []}

    counts = assignment.groupby("question_id").size()
    h1_ok = bool((counts == 1).all())
    report["checks"].append({"rule": "H1: every item assigned exactly once", "passed": h1_ok})

    req = required_counts(pool)
    actual = assignment.groupby(["competency_id", "optimized_booklet"]).size().to_dict()
    violations = []
    for (c, b), needed in req.items():
        got = actual.get((c, b), 0)
        if got != needed:
            violations.append(f"{c} in booklet {b}: required {needed}, got {got}")
    h2_ok = len(violations) == 0
    report["checks"].append({"rule": "H2: topic coverage matches required design",
                              "passed": h2_ok, "violations": violations})

    report["avg_difficulty_per_booklet"] = (
        assignment.groupby("optimized_booklet")["p_value"].mean().round(3).to_dict()
    )
    report["all_hard_rules_passed"] = h1_ok and h2_ok
    return report


def run_optimizer(pool: pd.DataFrame, time_limit: int = 60) -> dict:
    """
    The single entry point the service layer calls. Takes an item pool,
    returns the assignment plus a validation report - this is the only
    function outside this file that should ever be called directly.
    """
    model = build_model(pool)
    status, elapsed = solve(model, time_limit=time_limit)
    assignment = extract_assignment(model, pool)
    report = validate(assignment, pool)
    report["solver_status"] = status
    report["solve_time_seconds"] = elapsed

    avg_by_booklet = assignment.groupby("optimized_booklet")["p_value"].mean()
    spread = round(float(avg_by_booklet.max() - avg_by_booklet.min()), 4)

    return {
        "assignment": assignment,
        "report": report,
        "spread": spread,
    }
