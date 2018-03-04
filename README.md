# ynab-exporter

This is a Prometheus exporter for pulling data from YNAB. It's definitely rough around the edges, so use with caution.

To use this, you'll need a YNAB api key, and the id for the budget you want to pull data from.
Pass these in with env vars `YNAB_BUDGET_ID` and `YNAB_API_TOKEN`.
