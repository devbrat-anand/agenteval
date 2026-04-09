"""HTML reporter — detailed single-file report with reasoning visualization."""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

from agenteval.core.models import SuiteResult
from agenteval.reporting.base import Reporter


def _fmt_json(obj: Any) -> str:
    """Format an object as syntax-highlighted JSON."""
    try:
        raw = json.dumps(obj, indent=2, default=str)
    except (TypeError, ValueError):
        raw = str(obj)
    return html.escape(raw)


def _fmt_messages(messages: list[dict[str, Any]]) -> str:
    """Render a message list as readable HTML blocks."""
    parts: list[str] = []
    for msg in messages:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")

        # Bedrock Converse format: content is a list of blocks
        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict):
                    if "text" in block:
                        parts.append(
                            f'<div class="msg msg-{html.escape(role)}">'
                            f'<span class="msg-role">{html.escape(role)}</span>'
                            f'<span class="msg-text">{html.escape(str(block["text"]))}</span>'
                            f"</div>"
                        )
                    if "toolUse" in block:
                        tu = block["toolUse"]
                        parts.append(
                            f'<div class="msg msg-tool-use">'
                            f'<span class="msg-role">tool call</span>'
                            f'<span class="tool-name">{html.escape(tu.get("name", ""))}</span>'
                            f'<pre class="tool-args">{_fmt_json(tu.get("input", {}))}</pre>'
                            f"</div>"
                        )
                    if "toolResult" in block:
                        tr = block["toolResult"]
                        result_content = tr.get("content", "")
                        parts.append(
                            f'<div class="msg msg-tool-result">'
                            f'<span class="msg-role">tool result</span>'
                            f'<pre class="tool-output">{_fmt_json(result_content)}</pre>'
                            f"</div>"
                        )
                elif isinstance(block, str):
                    parts.append(
                        f'<div class="msg msg-{html.escape(role)}">'
                        f'<span class="msg-role">{html.escape(role)}</span>'
                        f'<span class="msg-text">{html.escape(block)}</span>'
                        f"</div>"
                    )
            continue

        # OpenAI format: content is a string
        content_str = html.escape(str(content)) if content else ""
        if content_str:
            parts.append(
                f'<div class="msg msg-{html.escape(role)}">'
                f'<span class="msg-role">{html.escape(role)}</span>'
                f'<span class="msg-text">{content_str}</span>'
                f"</div>"
            )

        # OpenAI tool_calls on assistant messages
        for tc in msg.get("tool_calls", []):
            fn = tc.get("function", {})
            parts.append(
                f'<div class="msg msg-tool-use">'
                f'<span class="msg-role">tool call</span>'
                f'<span class="tool-name">{html.escape(fn.get("name", ""))}</span>'
                f'<pre class="tool-args">{_fmt_json(fn.get("arguments", ""))}</pre>'
                f"</div>"
            )

    return "\n".join(parts)


class HtmlReporter(Reporter):
    def render(self, suite: SuiteResult, output_path: Path | None = None) -> None:
        # --- Summary rows ---
        summary_rows = ""
        for test in suite.tests:
            status_cls = "pass" if test.passed else "fail"
            status_text = "PASS" if test.passed else "FAIL"
            detail_rows = ""
            for er in test.eval_results:
                er_cls = "pass" if er.passed else "fail"
                detail_rows += (
                    f'<tr class="detail"><td>&nbsp;&nbsp;{html.escape(er.evaluator)}</td>'
                    f"<td>{er.score:.2f}</td><td></td><td></td>"
                    f'<td class="{er_cls}">{html.escape(er.reason)}</td></tr>\n'
                )
            summary_rows += (
                f'<tr><td><a href="#test-{id(test)}">{html.escape(test.test_name)}</a></td>'
                f"<td>{test.overall_score:.2f}</td>"
                f"<td>${test.trace.total_cost_usd:.6f}</td>"
                f"<td>{test.duration_ms:.0f}ms</td>"
                f"<td>{test.trace.total_input_tokens + test.trace.total_output_tokens}</td>"
                f'<td class="{status_cls}">{status_text}</td></tr>\n'
                f"{detail_rows}"
            )

        # --- Detailed test sections ---
        test_details = ""
        for test in suite.tests:
            status_cls = "pass" if test.passed else "fail"
            status_text = "PASS" if test.passed else "FAIL"
            trace = test.trace

            # Build turns visualization
            turns_html = ""
            for i, turn in enumerate(trace.turns, 1):
                llm_calls_html = ""
                for lc in turn.llm_calls:
                    llm_calls_html += (
                        f'<div class="llm-call">'
                        f'<div class="llm-header">'
                        f'<span class="llm-model">{html.escape(lc.model)}</span>'
                        f'<span class="llm-meta">'
                        f"{lc.input_tokens} in / {lc.output_tokens} out"
                        f" &middot; ${lc.cost_usd:.6f}"
                        f" &middot; {lc.latency_ms:.0f}ms"
                        f"</span>"
                        f"</div>"
                        f'<div class="llm-messages">{_fmt_messages(lc.messages)}</div>'
                        f'<div class="llm-response">'
                        f'<span class="msg-role">assistant</span>'
                        f'<span class="msg-text">{html.escape(lc.response)}</span>'
                        f"</div>"
                        f"</div>"
                    )

                tool_calls_html = ""
                for tc in turn.tool_calls:
                    result_str = (
                        _fmt_json(tc.result)
                        if tc.result is not None
                        else '<span class="no-result">no result captured</span>'
                    )
                    tool_calls_html += (
                        f'<div class="tool-call-detail">'
                        f'<div class="tool-call-header">'
                        f'<span class="tool-name">{html.escape(tc.name)}</span>'
                        f'<span class="tool-duration">{tc.duration_ms:.0f}ms</span>'
                        f"</div>"
                        f'<div class="tool-io">'
                        f'<div class="tool-section"><strong>Arguments</strong>'
                        f"<pre>{_fmt_json(tc.arguments)}</pre></div>"
                        f'<div class="tool-section"><strong>Result</strong>'
                        f"<pre>{result_str}</pre></div>"
                        f"</div>"
                        f"</div>"
                    )

                tc_section = (
                    f'<div class=tool-calls-section>'
                    f'<div class=tool-calls-label>Tool Calls</div>'
                    f'{tool_calls_html}</div>'
                    if tool_calls_html
                    else ''
                )
                turns_html += (
                    f'<div class="turn">'
                    f'<div class="turn-header">Turn {i}</div>'
                    f"{llm_calls_html}"
                    f"{tc_section}"
                    f"</div>"
                )

            if not trace.turns:
                turns_html = (
                    '<div class="no-turns">'
                    'No turns captured (interceptor may not have matched)'
                    '</div>'
                )

            # Build eval results section
            eval_results_html = ""
            if test.eval_results:
                eval_rows = ""
                for er in test.eval_results:
                    er_cls = "pass" if er.passed else "fail"
                    score_bar_width = max(0, min(100, int(er.score * 100)))
                    eval_rows += (
                        f'<div class="eval-row">'
                        f'<div class="eval-name">{html.escape(er.evaluator)}</div>'
                        f'<div class="eval-score-bar">'
                        f'<div class="eval-bar-fill {er_cls}"'
                        f' style="width:{score_bar_width}%">'
                        f'</div></div>'
                        f'<div class="eval-score-val {er_cls}">{er.score:.2f}</div>'
                        f'<div class="eval-reason">{html.escape(er.reason)}</div>'
                        f"</div>"
                    )
                eval_results_html = (
                    f'<div class="eval-section">'
                    f'<div class="eval-label">Evaluator Scores</div>'
                    f"{eval_rows}"
                    f"</div>"
                )

            test_details += f"""
<div class="test-detail" id="test-{id(test)}">
  <div class="test-header {status_cls}">
    <span class="test-status">{status_text}</span>
    <span class="test-name-detail">{html.escape(test.test_name)}</span>
    <span class="test-score">Score: {test.overall_score:.2f}</span>
  </div>
  <div class="test-meta">
    <span>Cost: ${trace.total_cost_usd:.6f}</span>
    <span>Latency: {trace.total_latency_ms:.0f}ms</span>
    <span>Tokens: {trace.total_input_tokens} in / {trace.total_output_tokens} out</span>
  </div>
  {eval_results_html}
  <div class="io-section">
    <div class="io-block">
      <div class="io-label">Input</div>
      <div class="io-content">{html.escape(trace.input)}</div>
    </div>
    <div class="io-block">
      <div class="io-label">Output</div>
      <div class="io-content">{html.escape(trace.output)}</div>
    </div>
  </div>
  <div class="reasoning-section">
    <div class="reasoning-label">Reasoning Trace</div>
    {turns_html}
  </div>
</div>"""

        generated_ts = suite.generated_at.strftime(
            "%Y-%m-%d %H:%M:%S UTC"
        )
        html_doc = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>agenteval Report</title>
<style>
  :root {{
    --bg: #0d1117; --surface: #161b22; --surface2: #21262d;
    --border: #30363d; --text: #e6edf3; --text-dim: #8b949e;
    --green: #3fb950; --red: #f85149; --blue: #58a6ff;
    --yellow: #d29922; --purple: #bc8cff; --cyan: #39d2c0;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
    background: var(--bg); color: var(--text);
    max-width: 1100px; margin: 0 auto; padding: 2rem 1.5rem;
    line-height: 1.5;
  }}
  h1 {{ font-size: 1.5rem; margin-bottom: 0.5rem; }}
  h2 {{
    font-size: 1.25rem; margin: 2rem 0 1rem;
    border-bottom: 1px solid var(--border);
    padding-bottom: 0.5rem;
  }}
  a {{ color: var(--blue); text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}

  /* Summary bar */
  .summary {{
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 8px; padding: 1rem 1.5rem; margin: 1rem 0 2rem;
    display: flex; gap: 1.5rem; flex-wrap: wrap; align-items: center;
  }}
  .summary .pass {{ color: var(--green); font-weight: 600; }}
  .summary .fail {{ color: var(--red); font-weight: 600; }}

  /* Summary table */
  table {{ width: 100%; border-collapse: collapse; margin: 1rem 0; }}
  th, td {{
    padding: 0.5rem 0.75rem; text-align: left;
    border-bottom: 1px solid var(--border);
    font-size: 0.875rem;
  }}
  th {{ background: var(--surface); color: var(--text-dim); font-weight: 600; }}
  td a {{ color: var(--blue); }}
  .pass {{ color: var(--green); font-weight: 600; }}
  .fail {{ color: var(--red); font-weight: 600; }}
  .detail td {{ color: var(--text-dim); font-size: 0.8rem; }}

  /* Test detail cards */
  .test-detail {{
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 8px; margin: 1.5rem 0; overflow: hidden;
  }}
  .test-header {{
    padding: 0.75rem 1.25rem; display: flex; align-items: center; gap: 0.75rem;
    border-bottom: 1px solid var(--border);
  }}
  .test-header.pass {{ border-left: 4px solid var(--green); }}
  .test-header.fail {{ border-left: 4px solid var(--red); }}
  .test-status {{ font-weight: 700; font-size: 0.8rem; letter-spacing: 0.05em; }}
  .test-header.pass .test-status {{ color: var(--green); }}
  .test-header.fail .test-status {{ color: var(--red); }}
  .test-name-detail {{ font-family: monospace; font-size: 0.85rem; color: var(--text-dim); }}

  .test-meta {{
    padding: 0.5rem 1.25rem; display: flex; gap: 1.5rem; flex-wrap: wrap;
    font-size: 0.8rem; color: var(--text-dim); border-bottom: 1px solid var(--border);
  }}

  /* Input / Output */
  .io-section {{ padding: 1rem 1.25rem; display: flex; gap: 1rem; flex-wrap: wrap; }}
  .io-block {{ flex: 1; min-width: 300px; }}
  .io-label {{
    font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.1em;
    color: var(--text-dim); margin-bottom: 0.35rem; font-weight: 600;
  }}
  .io-content {{
    background: var(--surface2); border: 1px solid var(--border);
    border-radius: 6px; padding: 0.75rem 1rem; font-size: 0.85rem;
    white-space: pre-wrap; word-break: break-word;
  }}

  /* Reasoning section */
  .reasoning-section {{ padding: 0 1.25rem 1.25rem; }}
  .reasoning-label {{
    font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.1em;
    color: var(--text-dim); margin-bottom: 0.75rem; font-weight: 600;
  }}

  /* Turns */
  .turn {{
    border: 1px solid var(--border); border-radius: 6px;
    margin-bottom: 0.75rem; overflow: hidden;
  }}
  .turn-header {{
    background: var(--surface2); padding: 0.4rem 0.75rem;
    font-size: 0.75rem; font-weight: 600; color: var(--text-dim);
    border-bottom: 1px solid var(--border);
  }}
  .no-turns {{
    color: var(--text-dim); font-size: 0.85rem; font-style: italic;
    padding: 0.5rem 0;
  }}

  /* LLM calls */
  .llm-call {{ padding: 0.75rem; }}
  .llm-header {{
    display: flex; justify-content: space-between; align-items: center;
    margin-bottom: 0.5rem;
  }}
  .llm-model {{
    font-family: monospace; font-size: 0.8rem; color: var(--purple);
    background: rgba(188,140,255,0.1); padding: 0.15rem 0.5rem;
    border-radius: 4px;
  }}
  .llm-meta {{ font-size: 0.75rem; color: var(--text-dim); }}

  /* Messages */
  .llm-messages {{ margin-bottom: 0.5rem; }}
  .msg {{
    padding: 0.5rem 0.75rem; margin: 0.25rem 0; border-radius: 6px;
    font-size: 0.85rem;
  }}
  .msg-role {{
    display: inline-block; font-size: 0.7rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: 0.05em;
    margin-right: 0.5rem; min-width: 60px;
  }}
  .msg-text {{ white-space: pre-wrap; word-break: break-word; }}
  .msg-user {{ background: rgba(88,166,255,0.08); }}
  .msg-user .msg-role {{ color: var(--blue); }}
  .msg-assistant {{ background: rgba(188,140,255,0.08); }}
  .msg-assistant .msg-role {{ color: var(--purple); }}
  .msg-system {{ background: rgba(210,153,34,0.08); }}
  .msg-system .msg-role {{ color: var(--yellow); }}
  .llm-response {{
    background: rgba(188,140,255,0.08); padding: 0.5rem 0.75rem;
    border-radius: 6px; font-size: 0.85rem;
  }}
  .llm-response .msg-role {{ color: var(--purple); }}
  .llm-response .msg-text {{ white-space: pre-wrap; word-break: break-word; }}

  /* Tool calls */
  .msg-tool-use {{
    background: rgba(57,210,192,0.08); border: 1px dashed rgba(57,210,192,0.3);
  }}
  .msg-tool-use .msg-role {{ color: var(--cyan); }}
  .msg-tool-result {{
    background: rgba(57,210,192,0.05); border: 1px solid rgba(57,210,192,0.15);
  }}
  .msg-tool-result .msg-role {{ color: var(--cyan); }}
  .tool-name {{
    font-family: monospace; font-weight: 600; color: var(--cyan);
    background: rgba(57,210,192,0.1); padding: 0.1rem 0.4rem; border-radius: 3px;
  }}
  .tool-args, .tool-output {{
    font-family: monospace; font-size: 0.8rem; margin-top: 0.35rem;
    background: var(--bg); padding: 0.5rem; border-radius: 4px;
    overflow-x: auto; white-space: pre-wrap; word-break: break-word;
  }}

  .tool-calls-section {{ padding: 0.5rem 0.75rem 0.75rem; border-top: 1px solid var(--border); }}
  .tool-calls-label {{
    font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.1em;
    color: var(--cyan); margin-bottom: 0.5rem; font-weight: 600;
  }}
  .tool-call-detail {{
    background: var(--surface2); border: 1px solid var(--border);
    border-radius: 6px; margin-bottom: 0.5rem; overflow: hidden;
  }}
  .tool-call-header {{
    display: flex; justify-content: space-between; align-items: center;
    padding: 0.4rem 0.75rem; border-bottom: 1px solid var(--border);
  }}
  .tool-duration {{ font-size: 0.75rem; color: var(--text-dim); }}
  .tool-io {{ padding: 0.5rem 0.75rem; }}
  .tool-section {{ margin-bottom: 0.5rem; }}
  .tool-section strong {{ font-size: 0.75rem; color: var(--text-dim); }}
  .tool-section pre {{ margin-top: 0.25rem; }}
  .no-result {{ color: var(--text-dim); font-style: italic; }}

  /* Eval results */
  .eval-section {{ padding: 0.75rem 1.25rem; border-bottom: 1px solid var(--border); }}
  .eval-label {{
    font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.1em;
    color: var(--text-dim); margin-bottom: 0.5rem; font-weight: 600;
  }}
  .eval-row {{
    display: grid; grid-template-columns: 140px 120px 40px 1fr;
    gap: 0.5rem; align-items: center; padding: 0.3rem 0;
    font-size: 0.8rem; border-bottom: 1px solid rgba(48,54,61,0.5);
  }}
  .eval-row:last-child {{ border-bottom: none; }}
  .eval-name {{ font-family: monospace; color: var(--text-dim); }}
  .eval-score-bar {{
    height: 6px; background: var(--surface2); border-radius: 3px; overflow: hidden;
  }}
  .eval-bar-fill {{
    height: 100%; border-radius: 3px; transition: width 0.3s;
  }}
  .eval-bar-fill.pass {{ background: var(--green); }}
  .eval-bar-fill.fail {{ background: var(--red); }}
  .eval-score-val {{ font-weight: 600; font-size: 0.8rem; }}
  .eval-reason {{ color: var(--text-dim); font-size: 0.75rem; }}
  .test-score {{ margin-left: auto; font-size: 0.8rem; color: var(--text-dim); }}

  /* Footer */
  footer {{
    margin-top: 2rem; padding-top: 1rem;
    border-top: 1px solid var(--border);
    font-size: 0.75rem; color: var(--text-dim);
  }}
</style></head><body>

<h1>agenteval Report</h1>
<div class="summary">
  <span class="pass">{suite.total_passed} passed</span>
  <span class="fail">{suite.total_failed} failed</span>
  <span>avg score: {suite.avg_score:.2f}</span>
  <span>total cost: ${suite.total_cost_usd:.6f}</span>
  <span>{suite.total_duration_ms:.0f}ms</span>
</div>

<h2>Summary</h2>
<table>
<tr><th>Test</th><th>Score</th><th>Cost</th><th>Time</th><th>Tokens</th><th>Status</th></tr>
{summary_rows}
</table>

<h2>Detailed Results</h2>
{test_details}

<footer>Generated by agenteval &middot; {generated_ts}</footer>
</body></html>"""

        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(html_doc)
        else:
            print(html_doc)
