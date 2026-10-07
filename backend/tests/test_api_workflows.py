import pytest

def test_list_seeded_datasets(client, viewer_auth):
    resp = client.get("/api/datasets", headers=viewer_auth["headers"])
    assert resp.status_code == 200
    datasets = resp.json()
    assert len(datasets) >= 2
    names = [d["name"] for d in datasets]
    assert any("Customer Risk" in n for n in names)
    assert any("Reasoning Quality" in n for n in names)

def test_full_dataset_and_prediction_workflow(client, analyst_auth):
    # 1. Create custom dataset
    create_ds_resp = client.post(
        "/api/datasets",
        json={
            "name": "Integration Test Benchmark",
            "description": "Dataset created during automated test run",
            "task_type": "classification",
            "target_column": "label",
            "cohort_columns": ["segment"],
        },
        headers=analyst_auth["headers"],
    )
    assert create_ds_resp.status_code == 201
    ds_id = create_ds_resp.json()["id"]

    # 2. Upload items
    items = [
        {"item_key": f"item_{i}", "ground_truth": "1" if i % 2 == 0 else "0", "cohorts": {"segment": "A" if i < 10 else "B"}}
        for i in range(20)
    ]
    upload_items_resp = client.post(
        f"/api/datasets/{ds_id}/items",
        json=items,
        headers=analyst_auth["headers"],
    )
    assert upload_items_resp.status_code == 200
    assert upload_items_resp.json()["uploaded_count"] == 20

    # 3. Create two model runs
    run_a = client.post(
        "/api/models",
        json={"dataset_id": ds_id, "name": "Model Alpha", "architecture": "CNN"},
        headers=analyst_auth["headers"],
    ).json()
    run_b = client.post(
        "/api/models",
        json={"dataset_id": ds_id, "name": "Model Beta", "architecture": "MLP"},
        headers=analyst_auth["headers"],
    ).json()

    # 4. Upload predictions
    preds_a = [{"item_key": f"item_{i}", "predicted_label": "1" if i % 2 == 0 else "0", "probability": 0.9} for i in range(20)]
    preds_b = [{"item_key": f"item_{i}", "predicted_label": "0", "probability": 0.3} for i in range(20)]

    client.post(f"/api/models/{run_a['id']}/predictions", json={"predictions": preds_a}, headers=analyst_auth["headers"])
    client.post(f"/api/models/{run_b['id']}/predictions", json={"predictions": preds_b}, headers=analyst_auth["headers"])

    # 5. Run arena evaluation
    eval_resp = client.post(
        "/api/evaluations/run",
        json={
            "dataset_id": ds_id,
            "model_run_ids": [run_a["id"], run_b["id"]],
            "resamples": 100,
            "confidence_level": 0.95,
        },
        headers=analyst_auth["headers"],
    )
    assert eval_resp.status_code == 200
    arena_data = eval_resp.json()
    assert len(arena_data["models"]) == 2
    assert len(arena_data["paired_tests"]) == 1
    report_id = arena_data["report_id"]
    assert report_id is not None

    # 6. Export report to JSON and CSV
    export_json = client.get(f"/api/evaluations/export/{report_id}?format=json", headers=analyst_auth["headers"])
    assert export_json.status_code == 200
    assert "application/json" in export_json.headers["content-type"]

    export_csv = client.get(f"/api/evaluations/export/{report_id}?format=csv", headers=analyst_auth["headers"])
    assert export_csv.status_code == 200
    assert "text/csv" in export_csv.headers["content-type"]
    assert "model_run_id" in export_csv.text

def test_llm_advisory_audit_offline_fallback(client, analyst_auth):
    # Retrieve classification benchmark
    ds = client.get("/api/datasets", headers=analyst_auth["headers"]).json()[0]
    models = client.get(f"/api/models?dataset_id={ds['id']}", headers=analyst_auth["headers"]).json()
    model_ids = [m["id"] for m in models[:2]]

    resp = client.post(
        "/api/llm/audit",
        json={
            "dataset_id": ds["id"],
            "model_run_ids": model_ids,
            "focus_metric": "accuracy",
        },
        headers=analyst_auth["headers"],
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "advisory_disclaimer" in data
    assert "[ADVISORY NOTICE]" in data["advisory_disclaimer"]
    assert data["status"] in ["offline_deterministic", "success"]
    assert "grounded_evidence" in data

def test_audit_logs_query(client, analyst_auth):
    resp = client.get("/api/audit", headers=analyst_auth["headers"])
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] > 0
    assert len(data["items"]) > 0
    actions = [item["action"] for item in data["items"]]
    assert any("create" in a or "run" in a or "upload" in a for a in actions)
