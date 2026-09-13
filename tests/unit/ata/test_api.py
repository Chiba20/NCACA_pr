from fastapi.testclient import TestClient

from ncaca.main import app


client = TestClient(app)


def test_optimize_submits_background_task(monkeypatch):
    class FakeTask:
        id = "test-task-123"

    def fake_apply_async(args):
        assert args == ["English", 60]
        return FakeTask()

    monkeypatch.setattr(
        "ncaca.api.v1.ata.optimize_ata_task.apply_async",
        fake_apply_async,
    )

    response = client.post(
        "/api/v1/ata/optimize",
        json={
            "subject": "English",
            "time_limit": 60,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["task_id"] == "test-task-123"
    assert body["status"] == "PENDING"
    assert body["message"] == "ATA optimization submitted successfully."

def test_get_task_status_pending(monkeypatch):
    class FakeAsyncResult:
        status = "PENDING"
        result = None

        def successful(self):
            return False

        def failed(self):
            return False

    monkeypatch.setattr(
        "ncaca.api.v1.ata.AsyncResult",
        lambda task_id, app: FakeAsyncResult(),
    )

    response = client.get(
        "/api/v1/ata/tasks/test-task-123"
    )

    assert response.status_code == 200

    body = response.json()

    assert body["task_id"] == "test-task-123"
    assert body["status"] == "PENDING"
    assert body["result"] is None
    assert body["error"] is None
