import pytest
from unittest.mock import MagicMock


class TestRegisterPluginTools:
    @pytest.fixture
    def mcp(self):
        return MagicMock()

    def test_registers_all_tools(self, mcp):
        from jenkins_mcp.registrations.plugin import register_tools
        register_tools(mcp)
        assert mcp.tool.call_count == 7
