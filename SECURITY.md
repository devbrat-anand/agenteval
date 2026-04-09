# Security Policy

## Supported Versions

| Version | Supported          |
|---------|--------------------|
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability in agenteval, please report it responsibly.

**Do not open a public GitHub issue.**

Instead, open a [security advisory](https://github.com/devbrat-anand/agenteval/security/advisories/new) or email the maintainer directly with:

- A description of the vulnerability
- Steps to reproduce
- Any relevant logs or screenshots

You will receive an acknowledgment within 48 hours and a detailed response within 5 business days.

## Scope

agenteval intercepts LLM API calls at the protocol level for testing purposes. Security concerns include:

- **Credential exposure** in test traces or reports
- **Injection attacks** via crafted agent outputs that affect evaluators
- **Data leakage** in HTML/JSON reports (PII from test runs)

## Best Practices

- Never commit API keys or credentials in `pyproject.toml` — use environment variables
- Review HTML reports before sharing — they contain full agent traces
- Use `--agenteval-report-dir` to control where reports are written
