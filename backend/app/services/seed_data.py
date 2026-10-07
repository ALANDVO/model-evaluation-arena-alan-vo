import json
import random
from sqlalchemy.orm import Session
from app.models.entities import Dataset, DatasetItem, ModelRun, Prediction

def seed_benchmarks_if_empty(db: Session) -> None:
    if db.query(Dataset).count() > 0:
        return

    rng = random.Random(1337)
    # 1. Classification Benchmark
    clf_ds = Dataset(
        name="Customer Risk & Churn Benchmark",
        description="Binary classification task evaluating predictive risk with demographic cohort slices and calibration tracking.",
        task_type="classification",
        target_column="churn",
        cohort_columns=json.dumps(["age_cohort", "region"]),
        created_by="system_seeder",
    )
    db.add(clf_ds); db.commit(); db.refresh(clf_ds)

    regions, ages = ["North America", "Europe", "APAC", "LATAM"], ["young_adult", "mid_career", "senior"]
    items_clf = []
    for i in range(1, 101):
        reg, age = regions[i % 4], ages[i % 3]
        churn = "1" if (i % 3 == 0 or (age == "senior" and i % 2 == 0)) else "0"
        key = f"cust_{i:04d}"
        db.add(DatasetItem(dataset_id=clf_ds.id, item_key=key, ground_truth=churn,
                           cohorts_json=json.dumps({"region": reg, "age_cohort": age}), metadata_json="{}"))
        items_clf.append((key, churn, age))
    db.commit()

    clf_specs = [
        ("Llama-3-70B-Classifier", "3.1-70B-Instruct", 0.90),
        ("Mistral-Large-Classifier", "Mistral-Large-2", 0.82),
        ("Logistic-Heuristic-Baseline", "Linear-Ridge", 0.68),
    ]
    for m_name, arch, acc_base in clf_specs:
        run = ModelRun(dataset_id=clf_ds.id, name=m_name, architecture=arch, created_by="seeder")
        db.add(run); db.commit(); db.refresh(run)
        for key, yt, age in items_clf:
            acc = acc_base - (0.20 if age == "senior" and "Logistic" in m_name else (0.12 if age == "senior" and "Mistral" in m_name else 0))
            is_correct = rng.random() < acc
            yp = yt if is_correct else ("1" if yt == "0" else "0")
            prob = rng.uniform(0.72, 0.96) if yp == "1" else rng.uniform(0.04, 0.28)
            db.add(Prediction(model_run_id=run.id, item_key=key, predicted_label=yp, probability=round(prob, 4)))
    db.commit()

    # 2. Regression Benchmark
    reg_ds = Dataset(
        name="LLM Reasoning Quality Scoring",
        description="Continuous evaluation score (1.0 to 5.0) measuring logical coherence and step accuracy across problem difficulties.",
        task_type="regression",
        target_column="score",
        cohort_columns=json.dumps(["difficulty_tier", "domain"]),
        created_by="system_seeder",
    )
    db.add(reg_ds); db.commit(); db.refresh(reg_ds)

    diffs, doms = ["basic_arithmetic", "multi_step_logic", "code_synthesis"], ["mathematics", "computer_science", "legal_reasoning"]
    items_reg = []
    for i in range(1, 81):
        diff, dom = diffs[i % 3], doms[i % 3]
        score = round(max(1.0, min(5.0, 3.0 + 1.5 * ((i % 17) / 17.0) - (0.5 if diff == "code_synthesis" else 0.0))), 2)
        key = f"eval_{i:04d}"
        db.add(DatasetItem(dataset_id=reg_ds.id, item_key=key, ground_truth=str(score),
                           cohorts_json=json.dumps({"difficulty_tier": diff, "domain": dom}), metadata_json="{}"))
        items_reg.append((key, score, diff))
    db.commit()

    reg_specs = [
        ("Qwen-2.5-72B-Judge", "Qwen-2.5-72B", 0.18),
        ("DeepSeek-V2.5-Judge", "DeepSeek-V2.5", 0.28),
        ("Rule-Length-Heuristic", "Heuristic-Count", 0.85),
    ]
    for m_name, arch, err_std in reg_specs:
        run = ModelRun(dataset_id=reg_ds.id, name=m_name, architecture=arch, created_by="seeder")
        db.add(run); db.commit(); db.refresh(run)
        for key, yt, diff in items_reg:
            noise = rng.gauss(0, err_std) + (0.8 if diff == "code_synthesis" and "Heuristic" in m_name else 0)
            pred = round(max(1.0, min(5.0, yt + noise)), 2)
            db.add(Prediction(model_run_id=run.id, item_key=key, predicted_label=str(pred)))
    db.commit()
