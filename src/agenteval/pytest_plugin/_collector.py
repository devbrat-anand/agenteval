"""Trace and eval result collector for the pytest plugin."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agenteval.core.models import EvalResult, Trace

_traces: list[Trace] = []
_eval_results: list[EvalResult] = []


def collect_trace(trace: Trace) -> None:
    _traces.append(trace)


def collect_eval_result(result: EvalResult) -> None:
    _eval_results.append(result)


def get_and_clear_traces() -> list[Trace]:
    result = list(_traces)
    _traces.clear()
    return result


def get_and_clear_eval_results() -> list[EvalResult]:
    result = list(_eval_results)
    _eval_results.clear()
    return result
