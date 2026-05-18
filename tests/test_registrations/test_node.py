import pytest
from unittest.mock import MagicMock


class TestRegisterNodeTools:
    @pytest.fixture
    def mcp(self):
        return MagicMock()

    def test_registers_all_tools(self, mcp):
        from jenkins_mcp.registrations.node import register_tools
        register_tools(mcp)
        assert mcp.tool.call_count == 9
