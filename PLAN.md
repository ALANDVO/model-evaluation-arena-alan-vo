# Product development plan

Each round completes one feature or repair. Future items are planned, not implemented claims.

## Current round

evaluation-report-comparison

## Roadmap

### evaluation-report-comparison — Evaluation Report Comparison View

Status: done

Acceptance:
- API endpoint to list all evaluation reports with filtering by dataset
- API endpoint to retrieve a specific evaluation report with full details
- Frontend component to display side-by-side comparison of multiple evaluation reports
- UI allows selecting multiple reports from same or different datasets for comparison
- Comparison shows metrics, bootstrap CIs, paired tests, and slice disparities across reports

Implementation: `backend/app/api/evaluations.py (added get_report_details endpoint)`, `frontend/src/api/client.ts (added getReportDetails and listReports methods)`, `frontend/src/components/EvaluationReportComparison.tsx (new component)`, `frontend/src/App.tsx (added compare tab)`, `frontend/src/components/Navbar.tsx (added Report Comparison nav button)`

Tests: `backend/tests/test_api_workflows.py (existing tests pass)`, `frontend/src/test/App.test.tsx (existing tests pass)`

