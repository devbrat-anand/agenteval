---
name: cost-audit
description: Audit AI agent API costs, identify expensive patterns
triggers:
  - "audit API spend"
  - "how much does this agent cost?"
  - "cost audit"
---

# Cost Audit

1. Use `agenteval show_cost_report` MCP tool
2. Run the agent with interception to capture per-turn costs
3. Identify expensive patterns (unnecessary LLM calls, large prompts, expensive models)
4. Suggest optimizations (model routing, prompt compression, caching)
