---
name: check-regression
description: Compare current agent against baseline, flag score and cost regressions
triggers:
  - "check for regressions"
  - "compare against baseline"
  - "regression test"
---

# Check Regression

1. Use `agenteval check_regression` MCP tool
2. Compare current scores vs. baseline
3. Flag any score drops > threshold or cost increases > 3x
4. Report findings with actionable suggestions
