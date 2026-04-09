---
name: eval-agent
description: Test an AI agent with agenteval — detect agent type, scaffold tests, run evaluations, report results
triggers:
  - "test this agent"
  - "run evals"
  - "evaluate this agent"
  - "is this agent reliable?"
---

# Eval Agent

## Steps

1. **Detect** — Scan the project for agent code. Look for imports from langchain, crewai, openai, anthropic, boto3, ollama. Identify the agent's entry point and what tools/providers it uses.

2. **Scaffold** — If no eval tests exist, generate them using `agenteval generate_test` MCP tool. Match evaluators to the agent type:
   - Tool-using agent → ToolCallEvaluator, LoopDetector, CostEvaluator
   - RAG agent → HallucinationEvaluator, ContextUtilizationEvaluator, SimilarityEvaluator
   - Customer-facing → GuardrailEvaluator, SecurityEvaluator
   - All agents → ConvergenceEvaluator, LatencyEvaluator

3. **Run** — Execute the eval suite using `agenteval run_eval` MCP tool.

4. **Report** — Present results inline. For failures, explain what went wrong and suggest fixes.

5. **Baseline** — If all tests pass, offer to save results as baseline using `agenteval save_baseline` MCP tool.
