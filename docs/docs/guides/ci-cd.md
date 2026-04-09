# CI/CD Integration

Run agent evaluations in your CI pipeline to catch failures before production.

## Quick Start: GitHub Actions

Use the official agenteval GitHub Action:

```yaml
# .github/workflows/agent-evals.yml
name: Agent Evals
on: [pull_request]

jobs:
  eval:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: devbrat-anand/agenteval@v1
        with:
          test_path: tests/agent_evals/
          fail_under: "0.8"
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

This runs your agent evals on every PR and fails if the overall score drops below 0.8.

## Manual Setup

If you want more control:

```yaml
name: Agent Evals
on:
  pull_request:
  push:
    branches: [main]

jobs:
  eval:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      
      - name: Install dependencies
        run: |
          pip install agenteval[all]
          pip install -r requirements.txt
      
      - name: Run agent evals
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: |
          agenteval run tests/agent_evals/ \
            --fail-under 0.8 \
            --report html \
            --report-dir reports/
      
      - name: Upload report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: eval-reports
          path: reports/
```

## Configuration Options

### Fail Thresholds

Block merges if scores drop below thresholds:

```yaml
- name: Run evals with thresholds
  run: |
    agenteval run tests/agent_evals/ \
      --fail-under 0.8 \               # Overall score
      --fail-under-cost 1.00 \         # Max cost per test ($)
      --fail-under-latency 30000       # Max latency (ms)
```

### Reports

Generate HTML, JSON, or JUnit reports:

```yaml
- name: Run evals with reports
  run: |
    agenteval run tests/agent_evals/ \
      --report html \
      --report json \
      --report junit \
      --report-dir reports/
```

### PR Comments

Post results as PR comments:

```yaml
- name: Run evals
  id: evals
  run: |
    agenteval run tests/agent_evals/ \
      --report json \
      --report-dir reports/
  continue-on-error: true

- name: Comment PR
  uses: actions/github-script@v7
  with:
    script: |
      const fs = require('fs');
      const report = JSON.parse(fs.readFileSync('reports/report.json', 'utf8'));
      
      const body = `## Agent Evals Results
      
      | Metric | Value |
      |--------|-------|
      | Overall Score | ${report.overall_score.toFixed(2)} |
      | Tests Passed | ${report.passed}/${report.total} |
      | Total Cost | $${report.total_cost.toFixed(4)} |
      | Avg Latency | ${report.avg_latency}ms |
      
      ${report.overall_score < 0.8 ? '⚠️ Score below threshold (0.8)' : '✅ All checks passed'}
      `;
      
      github.rest.issues.createComment({
        issue_number: context.issue.number,
        owner: context.repo.owner,
        repo: context.repo.repo,
        body: body
      });
```

## Regression Baselines

Track performance over time and catch regressions:

### 1. Generate baseline

On your main branch:

```bash
agenteval run tests/agent_evals/ --save-baseline baseline.json
```

Commit `baseline.json` to your repo.

### 2. Compare against baseline

In CI:

```yaml
- name: Run evals with baseline
  run: |
    agenteval run tests/agent_evals/ \
      --baseline baseline.json \
      --fail-on-regression
```

This fails if:
- Overall score drops by >5%
- Any test cost increases by >20%
- Any test latency increases by >30%

### 3. Update baseline

When you intentionally change behavior:

```bash
agenteval run tests/agent_evals/ --save-baseline baseline.json --force
git add baseline.json
git commit -m "Update eval baseline"
```

## Cost Limits

Prevent runaway costs in CI:

```yaml
- name: Run evals with cost limit
  run: |
    agenteval run tests/agent_evals/ \
      --max-total-cost 5.00     # Abort if total cost exceeds $5
```

**Tip**: Use Ollama for $0 eval costs. See [$0 Local Evals](local-evals.md).

## Provider Credentials

### OpenAI

```yaml
env:
  OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

Add the secret: Settings → Secrets → Actions → New repository secret

### AWS Bedrock

```yaml
env:
  AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
  AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
  AWS_REGION: us-east-1
```

## Parallel Execution

Speed up CI by running tests in parallel:

```yaml
- name: Run evals in parallel
  run: |
    agenteval run tests/agent_evals/ -n auto  # Auto-detect CPUs
```

Or with pytest-xdist:

```yaml
- name: Install parallel support
  run: pip install pytest-xdist

- name: Run evals
  run: pytest tests/agent_evals/ -n 4 -v
```

## Conditional Execution

Only run evals when agent code changes:

```yaml
name: Agent Evals
on:
  pull_request:
    paths:
      - 'src/agent/**'
      - 'tests/agent_evals/**'
      - 'pyproject.toml'
```

## Full Example: Production CI

```yaml
name: Agent Evals
on:
  pull_request:
  push:
    branches: [main]

jobs:
  eval:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: "pip"
      
      - name: Install Ollama (for $0 evals)
        run: |
          curl -fsSL https://ollama.ai/install.sh | sh
          ollama serve &
          sleep 5
          ollama pull llama3.2
      
      - name: Install dependencies
        run: |
          pip install agenteval[all]
          pip install -r requirements.txt
      
      - name: Run agent evals
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          AGENTEVAL_EVAL_PROVIDER: ollama
          AGENTEVAL_EVAL_MODEL: llama3.2
        run: |
          agenteval run tests/agent_evals/ \
            --baseline baseline.json \
            --fail-on-regression \
            --fail-under 0.8 \
            --max-total-cost 2.00 \
            --report html \
            --report json \
            --report-dir reports/ \
            -v
      
      - name: Upload reports
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: eval-reports
          path: reports/
          retention-days: 30
      
      - name: Comment PR
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const report = JSON.parse(fs.readFileSync('reports/report.json', 'utf8'));
            
            const body = `## Agent Evals Results
            
            | Metric | Value | Status |
            |--------|-------|--------|
            | Overall Score | ${report.overall_score.toFixed(2)} | ${report.overall_score >= 0.8 ? '✅' : '❌'} |
            | Tests Passed | ${report.passed}/${report.total} | ${report.passed === report.total ? '✅' : '⚠️'} |
            | Total Cost | $${report.total_cost.toFixed(4)} | ${report.total_cost < 2.00 ? '✅' : '❌'} |
            | Avg Latency | ${report.avg_latency}ms | ℹ️ |
            | Regression | ${report.regression ? 'Detected' : 'None'} | ${report.regression ? '❌' : '✅'} |
            
            [Full Report](https://github.com/${{ github.repository }}/actions/runs/${{ github.run_id }})
            `;
            
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: body
            });
```

## GitLab CI

```yaml
# .gitlab-ci.yml
agent-evals:
  stage: test
  image: python:3.12
  before_script:
    - pip install agenteval[all]
    - pip install -r requirements.txt
  script:
    - |
      agenteval run tests/agent_evals/ \
        --fail-under 0.8 \
        --report html \
        --report-dir reports/
  artifacts:
    when: always
    paths:
      - reports/
    expire_in: 30 days
  variables:
    OPENAI_API_KEY: $OPENAI_API_KEY
```

## CircleCI

```yaml
# .circleci/config.yml
version: 2.1

jobs:
  agent-evals:
    docker:
      - image: cimg/python:3.12
    steps:
      - checkout
      - run:
          name: Install dependencies
          command: |
            pip install agenteval[all]
            pip install -r requirements.txt
      - run:
          name: Run agent evals
          command: |
            agenteval run tests/agent_evals/ \
              --fail-under 0.8 \
              --report junit \
              --report-dir reports/
      - store_test_results:
          path: reports/
      - store_artifacts:
          path: reports/

workflows:
  test:
    jobs:
      - agent-evals
```

## Jenkins

```groovy
pipeline {
    agent any
    
    environment {
        OPENAI_API_KEY = credentials('openai-api-key')
    }
    
    stages {
        stage('Setup') {
            steps {
                sh 'pip install agenteval[all]'
                sh 'pip install -r requirements.txt'
            }
        }
        
        stage('Run Agent Evals') {
            steps {
                sh '''
                    agenteval run tests/agent_evals/ \
                        --fail-under 0.8 \
                        --report html \
                        --report junit \
                        --report-dir reports/
                '''
            }
        }
    }
    
    post {
        always {
            junit 'reports/junit.xml'
            publishHTML([
                reportDir: 'reports',
                reportFiles: 'index.html',
                reportName: 'Agent Eval Report'
            ])
        }
    }
}
```

## Best Practices

### 1. Use $0 local evals in CI

Use Ollama for evaluation to avoid API costs:

```yaml
env:
  AGENTEVAL_EVAL_PROVIDER: ollama
  AGENTEVAL_EVAL_MODEL: llama3.2
```

See [$0 Local Evals](local-evals.md).

### 2. Set cost limits

Prevent runaway costs:

```yaml
run: agenteval run tests/agent_evals/ --max-total-cost 5.00
```

### 3. Track baselines

Commit `baseline.json` and use `--fail-on-regression` to catch performance drops.

### 4. Upload reports

Always upload reports as artifacts:

```yaml
- uses: actions/upload-artifact@v4
  if: always()
  with:
    name: eval-reports
    path: reports/
```

### 5. Run on schedule

Catch drift with nightly runs:

```yaml
on:
  schedule:
    - cron: '0 2 * * *'  # 2 AM daily
```

## Troubleshooting

### "API rate limit exceeded"

**Problem**: Too many concurrent eval calls.

**Solution**:
1. Use Ollama for evals (no rate limits)
2. Add delays: `agenteval run --rate-limit 10`  # Max 10 req/sec
3. Use a dedicated eval API key with higher limits

### "Job timeout"

**Problem**: Evals take too long.

**Solution**:
1. Increase timeout: `timeout-minutes: 60`
2. Run in parallel: `agenteval run -n auto`
3. Split into multiple jobs
4. Use faster eval model (Ollama `mistral`)

### "Baseline not found"

**Problem**: `baseline.json` not in repo.

**Solution**:
```bash
agenteval run tests/agent_evals/ --save-baseline baseline.json
git add baseline.json
git commit -m "Add eval baseline"
```

## Next Steps

- [$0 Local Evals](local-evals.md) — Eliminate eval costs in CI
- [Provider Setup](providers.md) — Configure cloud provider credentials
- [Custom Evaluators](custom-evaluators.md) — Write CI-specific evaluators
