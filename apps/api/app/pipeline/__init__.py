"""Editing pipeline package. The job orchestrator lives in `orchestrator.py`;
leaf stage modules (highlight, select, signals, ...) stay importable without
pulling in the DB engine or heavy deps."""
