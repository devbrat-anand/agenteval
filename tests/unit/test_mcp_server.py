from agenteval.mcp.server import TOOL_DEFINITIONS, create_server


def test_server_has_8_tools():
    assert len(TOOL_DEFINITIONS) == 8


def test_tool_names():
    names = {t["name"] for t in TOOL_DEFINITIONS}
    expected = {
        "run_eval",
        "run_single_test",
        "check_regression",
        "show_cost_report",
        "list_evaluators",
        "generate_test",
        "save_baseline",
        "explain_failure",
    }
    assert names == expected


def test_all_tools_have_description():
    for tool in TOOL_DEFINITIONS:
        assert "description" in tool
        assert len(tool["description"]) > 10


def test_create_server_returns_server():
    server = create_server()
    assert server is not None
