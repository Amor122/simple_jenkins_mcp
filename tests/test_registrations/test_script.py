import pytest
from unittest.mock import MagicMock


class TestRegisterScriptTools:
    @pytest.fixture
    def mcp(self):
        return MagicMock()

    def test_registers_all_tools(self, mcp):
        from jenkins_mcp.registrations.script import register_tools
        register_tools(mcp)
        assert mcp.tool.call_count == 13
