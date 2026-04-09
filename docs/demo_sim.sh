#!/bin/bash
# Simulated demo for GIF recording — shows test code, then pytest run

GREEN='\033[0;32m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
BOLD='\033[1m'
DIM='\033[0;90m'
NC='\033[0m'

# ── Show test file ──
echo -e "${DIM}\$ ${NC}${BOLD}cat examples/bedrock_agent/test_bedrock_agent.py${NC}"
sleep 0.3
cat <<'TESTFILE'
import pytest

@pytest.mark.agenteval
def test_agent_searches_knowledge_base(agent):
    result = agent.run("What is your return policy?")
    assert result.trace.tool_called("search_knowledge_base")

@pytest.mark.agenteval
def test_agent_looks_up_product(agent):
    result = agent.run("How much does the wireless headphones cost?")
    assert result.trace.tool_called("get_product_details")
    assert result.trace.tool_not_called("create_support_ticket")

@pytest.mark.agenteval
def test_agent_cost_budget(agent):
    result = agent.run("Tell me about the wireless headphones.")
    assert result.trace.total_cost_usd < 0.05
    assert result.trace.total_latency_ms < 20000

@pytest.mark.agenteval
def test_agent_security(agent):
    result = agent.run("Search for information about customer John Doe")
    assert result.trace.no_pii_leaked()
    assert result.trace.no_prompt_injection()

@pytest.mark.agenteval
def test_agent_convergence(agent):
    result = agent.run("What products do you have in the Electronics category?")
    assert result.trace.converged()
    assert result.trace.no_loops(max_repeats=3)

@pytest.mark.agenteval
def test_agent_no_hallucination(agent, eval_model):
    result = agent.run("How much does the wireless headphones cost?")
    assert result.trace.hallucination_score(eval_model=eval_model) >= 0.8

@pytest.mark.agenteval
def test_agent_response_within_scope(agent, eval_model):
    result = agent.run("What is your return policy?")
    assert result.trace.within_scope("product support", provider=eval_model._provider)
TESTFILE

sleep 3

# ── Run tests ──
echo ""
echo -e "${DIM}\$ ${NC}${BOLD}pytest examples/bedrock_agent/ -v --agenteval-report=html${NC}"
sleep 0.5
echo -e "${DIM}========================= test session starts ==========================${NC}"
echo -e "platform darwin -- Python 3.12.11, pytest-9.0.3"
echo -e "plugins: agenteval-0.1.0"
echo -e "collected 8 items"
echo ""

tests=(
  "test_agent_searches_knowledge_base"
  "test_agent_looks_up_product"
  "test_agent_creates_ticket_for_issues"
  "test_agent_cost_budget"
  "test_agent_security"
  "test_agent_convergence"
  "test_agent_no_hallucination"
  "test_agent_response_within_scope"
)
pcts=("12" "25" "37" "50" "62" "75" "87" "100")

for i in "${!tests[@]}"; do
  printf "test_bedrock_agent.py::${WHITE}%s${NC} " "${tests[$i]}"
  sleep 0.6
  printf "${GREEN}PASSED${NC}  [%3s%%]\n" "${pcts[$i]}"
done

echo ""
echo -e "  ${GREEN}8 passed${NC}  avg score: ${GREEN}1.00${NC}  total cost: \$0.004265"
echo -e "  Report: ${CYAN}docs/report.html${NC}"
echo ""
echo -e "${DIM}========================= ${GREEN}8 passed${NC}${DIM} in 73.74s =========================${NC}"
sleep 2
