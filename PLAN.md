# Product development plan

Each round completes one feature or repair. Future items are planned, not implemented claims.

## Current round

evaluation-report-comparison-test

## Roadmap

### continue-implementation — Continue implementation and resolve known failures

Status: done

Acceptance:
- Run checks, fix failures, and implement the next planned feature

Tests: `backend/tests/test_api_workflows.py (all 24 tests pass)`, `frontend/src/test/App.test.tsx (all 5 tests pass)`

### evaluation-report-comparison-test — Add frontend test for EvaluationReportComparison component

Status: done

Acceptance:
- Test renders EvaluationReportComparison with metrics table showing bootstrap CIs
- Test verifies paired tests section displays significance results
- Test verifies slice disparities section shows cohort breakdowns and worst slice
- Test verifies export buttons (JSON and CSV) are present

Implementation: `frontend/src/test/App.test.tsx (added test for EvaluationReportComparison)`

Tests: `frontend/src/test/App.test.tsx (5 tests total, all pass)`

---

Alan Vo · [alanvo.net](https://alanvo.net) · [X: @alanvoasi](https://x.com/alanvoasi)
