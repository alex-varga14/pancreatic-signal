"""Backwards-compatible re-export of the SQLAlchemy-backed case store.

The implementation now lives in :mod:`app.store.case_store`; this module is
preserved as a thin shim to keep historical import sites
(``from app.store.memory_store import CASE_STORE`` / ``SqlAlchemyCaseStore``)
working without churn. New code should import from
:mod:`app.store.case_store` directly.
"""

from __future__ import annotations

from app.store.case_store import CASE_STORE, SqlAlchemyCaseStore

__all__ = ["CASE_STORE", "SqlAlchemyCaseStore"]
