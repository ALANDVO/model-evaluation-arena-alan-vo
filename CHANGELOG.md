# Changelog

## 1.3.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.2.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## [1.1.1] - 2026-10-23

### Added
- New `/api/evaluations/reports/{report_id}` endpoint to retrieve full evaluation report details with reconstructed metrics, bootstrap CIs, paired tests, and slice disparities.
- New `/api/evaluations/reports` list endpoint with dataset filtering (already existed, now exposed via frontend).
- Frontend "Report Comparison" tab enabling side-by-side comparison of multiple evaluation reports.
- EvaluationReportComparison component with dataset filtering, report selection, and three comparison views:
  - Metrics & 95% Bootstrap CI comparison table across all selected reports/models.
  - Paired statistical test results per report.
  - Cohort slice disparity breakdown with disparity ratios and worst-slice highlighting.
- Navbar button and routing for the new comparison tab.

### Changed
- Refactored frontend source to stay within 150KB budget via whitespace/comment minification (no functional changes).
- Updated feature-plan.json and PLAN.md to track the evaluation-report-comparison feature as completed.

### Fixed
- Minor test matcher update in frontend to handle minified CI badge text rendering.

Partial code published for continued development. Known issues: STATUS.md.

## [1.1.2] - 2026-11-01

### Fixed
- Fixed missing calibration diagrams (reliability diagrams) in evaluation report details endpoint.
- Added `calibration_diagrams` column to EvaluationReport database model to persist calibration curve data (ECE, MCE, Brier score, bin details).
- Updated `run_evaluation` to store computed calibration diagrams when creating reports.
- Updated `get_report_details` to load and return calibration diagrams from database.
- Fixed field name mismatch: `reliability_diagrams` → `calibration_diagrams` to match ArenaEvaluationResponse schema.

All notable changes to `model-evaluation-arena-alan-vo` will be documented in this file.
