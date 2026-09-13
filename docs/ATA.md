# Automated Test Assembly (ATA)

## Purpose

The ATA component creates balanced assessment booklets while preserving the required competency coverage. ATA starts from already-scored student responses; scoring raw responses is outside the ATA component.

## Input Assumptions

ATA uses:

1. Already-scored student responses, where question responses are represented as 0/1 values.
2. Item mapping metadata containing:
   - booklet
   - question number
   - subject
   - question ID
   - competency ID
3. Only responses with `Status == "scored"` are used for item analysis.
4. Biology and Computer Studies optional-subject responses are filtered using the student's optional subject.

## Item Difficulty

Item difficulty is represented using the p-value:

p-value = number of correct responses / number of attempted responses

A higher p-value represents an easier item, while a lower p-value represents a harder item.

## ATA Workflow

The implemented flow is:

Already-scored responses
-> item analysis and p-value calculation
-> subject item pool
-> heuristic baseline
-> Pyomo/HiGHS optimization
-> validation
-> balanced booklet assignment

The heuristic provides a baseline assignment based on item difficulty while preserving competency counts.

The formal optimizer uses Pyomo with the HiGHS solver. Each item must be assigned to exactly one booklet, and the required number of items for each competency in each booklet is preserved. The optimization objective reduces differences in total item difficulty between booklets.

## Architecture

The ATA implementation follows the backend layered architecture:

- `ncaca/api/v1/ata.py` - FastAPI HTTP routes
- `ncaca/services/ata/ata_service.py` - ATA business orchestration
- `ncaca/services/ata/item_analysis.py` - item difficulty analysis
- `ncaca/services/ata/heuristic.py` - heuristic baseline
- `ncaca/services/ata/optimizer.py` - Pyomo/HiGHS optimization
- `ncaca/repositories/ata_repository.py` - ATA data-access boundary
- `ncaca/workers/tasks/ata_tasks.py` - Celery background optimization task

## Background Execution

Optimization is submitted through FastAPI as a Celery background task.

FastAPI -> Redis -> Celery worker -> ATA service -> Pyomo/HiGHS

The API returns a task ID immediately. The client can then query the task-status endpoint to obtain the completed optimization result.

## API

- `GET /api/v1/ata/subjects`
- `GET /api/v1/ata/competencies/{competency_id}`
- `POST /api/v1/ata/optimize`
- `GET /api/v1/ata/tasks/{task_id}`

## Output Assumptions

The optimization result includes:

- subject
- number of assigned items
- average difficulty per booklet
- difficulty spread
- solver status
- validation result for the hard constraints

A feasible solution is accepted only when the hard assignment and competency-coverage rules pass validation.

Reaching the solver time limit does not by itself prove global optimality. A solution returned at the time limit may still be feasible and valid if all hard constraints pass.

## Current Data Access

The current development implementation loads ATA mapping and p-value files through the repository layer using local CSV paths. Paths can be overridden using environment variables.

This keeps data access separated from the ATA service and optimizer so the repository implementation can later be replaced with database-backed access without changing the optimization logic.

Local ATA assessment data under `data/ata/` is excluded from Git and must not be committed.
