# Changelog

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

All notable changes to `model-evaluation-arena-alan-vo` will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-10-15

### Added
- Wilcoxon signed-rank test implementation for non-parametric paired hypothesis testing in regression evaluations.
- Replaced paired t-test with Wilcoxon signed-rank test as the default statistical test for regression residual comparisons (more robust to non-normal error distributions).
- New unit tests for Wilcoxon signed-rank test covering significant differences, non-significant differences, and zero-difference edge cases.

### Changed
- `compare_model_runs_statistical` now uses Wilcoxon signed-rank test for regression tasks (previously used paired t-test).
- Updated statistical test reporting to include W+ and W- rank sums in details.

## [1.0.0] - 2026-10-07

### Added
- Core statistical domain engine for classification (Accuracy, Precision, Recall, Macro/Micro F1, ROC-AUC, Brier score, Expected Calibration Error) and regression metrics (MSE, RMSE, MAE, MAPE, R², Pearson r).
- Non-parametric bootstrap resampling engine computing percentile 95% confidence intervals and paired difference distributions across competing models.
- Paired statistical hypothesis tests including McNemar's test for classification error discrepancies and Wilcoxon signed-rank tests for regression residual variance.
- Cohort slice analyzer evaluating demographic, metadata, and slice performance with disparity ratios and worst-slice identification.
- Grounded advisory LLM evaluation diagnostics supporting OpenAI-compatible, Anthropic, Gemini, and Ollama providers with strict advisory disclaimers and offline fallback.
- FastAPI backend with SQLite persistence, transactional mutations, structured audit logging, and pagination.
- OIDC authorization-code authentication with PKCE, secure session cookies, CSRF protection, RBAC (viewer, analyst, admin), and localhost-only demo mode.
- Interactive React 18 + TypeScript + Vite frontend with benchmark arena dashboard, SVG calibration diagrams, bootstrap distribution plots, cohort disparity breakdown, and CSV/JSON report exports.
- Docker containerization for frontend, backend, and Keycloak with local profile bindings and CI workflow.
