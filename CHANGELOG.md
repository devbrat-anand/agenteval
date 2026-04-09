# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-04-09

### Added

- Core data models: Trace, LLMCall, ToolCall, Turn, EvalResult, TestResult, SuiteResult
- InterceptorRegistry with auto-detection of installed SDKs
- 5 provider interceptors: OpenAI, AWS Bedrock, Google Vertex AI, Azure OpenAI, Anthropic
- PricingEngine with bundled pricing data for all providers
- 13 built-in evaluators:
  - Structural: ToolCall, Cost, Latency, LoopDetector, OutputStructure
  - Semantic: LLMJudge, Hallucination, Similarity
  - Safety: Security, Guardrail
  - Operational: Regression, Convergence, ContextUtilization
- Evaluator plugin interface with Python entry point discovery
- Eval model providers: OpenAI and Ollama ($0 local evals)
- pytest plugin with fixtures, markers, and CLI flags
- Trace convenience assertions (tool_called, no_loops, no_pii_leaked, etc.)
- CLI: `agenteval run`, `agenteval init`, `agenteval version`
- MCP server with 8 tools + `agenteval mcp serve/install`
- 6 cross-platform skills with adapters for Claude Code, Copilot, Cursor, Windsurf
- 3 report formats: console (rich), HTML, JSON
- GitHub Action with PR comment bot
- CI/CD: GitHub Actions for testing + PyPI publishing via Trusted Publisher
- 5 example projects: quickstart, OpenAI, Bedrock, LangChain, Ollama
- mkdocs documentation site
- CONTRIBUTING.md with evaluator/interceptor contribution guides
