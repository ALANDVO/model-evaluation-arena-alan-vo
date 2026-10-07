# Changelog

All notable changes to `model-evaluation-arena-alan-vo` will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
