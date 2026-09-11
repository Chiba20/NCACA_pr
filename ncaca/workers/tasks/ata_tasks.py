from ncaca.repositories.ata_repository import load_mapping_and_pvalues
from ncaca.services.ata.ata_service import run_ata_optimization
from ncaca.workers.celery_app import celery_app


@celery_app.task(name="ncaca.ata.optimize")
def optimize_ata_task(subject: str, time_limit: int = 60):
    """
    Run ATA optimization as a Celery background job.

    The task loads the current ATA inputs through the repository layer,
    calls the ATA service layer, and returns only JSON-serializable values.
    """
    mapping_df, pvalue_df = load_mapping_and_pvalues()

    return run_ata_optimization(
        mapping_df=mapping_df,
        pvalue_df=pvalue_df,
        subject=subject,
        time_limit=time_limit,
    )
