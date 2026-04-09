---
name: security-audit
description: Check agent for security vulnerabilities — PII leaks, injections, credential exposure
triggers:
  - "check security"
  - "is this agent safe?"
  - "security audit"
---

# Security Audit

1. Run the agent with various test prompts
2. Use SecurityEvaluator to check for: PII leakage, credential exposure, prompt injection, SQL injection
3. Use GuardrailEvaluator to check for: scope violations, toxic content
4. Report vulnerabilities with severity and fix suggestions
