"""Built-in evaluators for agenteval."""

from agenteval.evaluators.base import (
    Evaluator,
    EvaluatorRegistry,
    default_evaluator_registry,
)
from agenteval.evaluators.context_utilization import ContextUtilizationEvaluator
from agenteval.evaluators.convergence import ConvergenceEvaluator
from agenteval.evaluators.cost import CostEvaluator
from agenteval.evaluators.guardrail import GuardrailEvaluator
from agenteval.evaluators.hallucination import HallucinationEvaluator
from agenteval.evaluators.latency import LatencyEvaluator
from agenteval.evaluators.llm_judge import LLMJudgeEvaluator
from agenteval.evaluators.loop_detector import LoopDetectorEvaluator
from agenteval.evaluators.output_structure import OutputStructureEvaluator
from agenteval.evaluators.regression import RegressionEvaluator
from agenteval.evaluators.security import SecurityEvaluator
from agenteval.evaluators.similarity import SimilarityEvaluator
from agenteval.evaluators.tool_call import ToolCallEvaluator

# Register all built-in evaluators
default_evaluator_registry.register(ToolCallEvaluator)
default_evaluator_registry.register(CostEvaluator)
default_evaluator_registry.register(LatencyEvaluator)
default_evaluator_registry.register(LoopDetectorEvaluator)
default_evaluator_registry.register(OutputStructureEvaluator)
default_evaluator_registry.register(LLMJudgeEvaluator)
default_evaluator_registry.register(HallucinationEvaluator)
default_evaluator_registry.register(SimilarityEvaluator)
default_evaluator_registry.register(SecurityEvaluator)
default_evaluator_registry.register(GuardrailEvaluator)
default_evaluator_registry.register(RegressionEvaluator)
default_evaluator_registry.register(ConvergenceEvaluator)
default_evaluator_registry.register(ContextUtilizationEvaluator)

__all__ = [
    "Evaluator",
    "EvaluatorRegistry",
    "default_evaluator_registry",
    "ToolCallEvaluator",
    "CostEvaluator",
    "LatencyEvaluator",
    "LoopDetectorEvaluator",
    "OutputStructureEvaluator",
    "LLMJudgeEvaluator",
    "HallucinationEvaluator",
    "SimilarityEvaluator",
    "SecurityEvaluator",
    "GuardrailEvaluator",
    "RegressionEvaluator",
    "ConvergenceEvaluator",
    "ContextUtilizationEvaluator",
]
