---
name: generate-tests
description: Generate eval test files for an AI agent with appropriate evaluators
triggers:
  - "generate eval tests"
  - "write tests for this agent"
  - "create agent tests"
---

# Generate Tests

1. Analyze the agent code — identify provider, tools, expected behavior
2. Use `agenteval generate_test` MCP tool to scaffold a test file
3. Customize the generated test with project-specific assertions
4. Run the tests to verify they work
