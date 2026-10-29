"""
core.validation — CPCV meta-methodology for strategy validation.

Public API
----------
from core.validation.cpcv import run_cpcv
from core.validation.multi_test import deflated_sharpe, harvey_liu_bhy
from core.validation.pipeline import generate_cpcv_report
"""
from core.validation.cpcv import run_cpcv
from core.validation.multi_test import deflated_sharpe, harvey_liu_bhy
from core.validation.pipeline import generate_cpcv_report

__all__ = ["run_cpcv", "deflated_sharpe", "harvey_liu_bhy", "generate_cpcv_report"]
