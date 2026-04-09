"""Token pricing engine for cost computation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class PricingEngine:
    """Computes cost from token counts using a bundled pricing table."""

    def __init__(self, pricing_path: Path | None = None) -> None:
        if pricing_path is not None:
            with open(pricing_path) as f:
                self._table: dict[str, dict[str, Any]] = json.load(f)
        else:
            data_file = Path(__file__).parent / "data" / "pricing.json"
            with open(data_file) as f:
                self._table = json.load(f)

    def compute_cost(
        self,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
    ) -> float:
        provider_table = self._table.get(provider, {})
        model_pricing = provider_table.get(model)
        if model_pricing is None:
            model_pricing = provider_table.get("_default")
        if model_pricing is None:
            return 0.0

        input_cost = (input_tokens / 1_000_000) * float(model_pricing["input_per_1m"])
        output_cost = (output_tokens / 1_000_000) * float(model_pricing["output_per_1m"])
        return float(round(input_cost + output_cost, 8))

    def available_providers(self) -> list[str]:
        return list(self._table.keys())
