"""Unit tests for pytest plugin integration."""


def test_plugin_provides_agent_runner_fixture(pytestconfig):
    """Test that the agenteval plugin is registered and provides fixtures."""
    plugin_manager = pytestconfig.pluginmanager
    assert plugin_manager.has_plugin("agenteval")
