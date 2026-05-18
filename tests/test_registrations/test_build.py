import pytest
from unittest.mock import MagicMock, patch


class TestRegisterBuildTools:
    @pytest.fixture
    def mcp(self):
        return MagicMock()

    def test_registers_all_tools(self, mcp):
        from jenkins_mcp.registrations.build import register_tools
        register_tools(mcp)
        assert mcp.tool.call_count == 12

    def test_get_build_console_output_offset(self, mcp):
        from jenkins_mcp.registrations.build import register_tools
        register_tools(mcp)

        mock_jk = MagicMock()
        mock_jk.get_build_console_output.return_value = 'a\nb\nc\nd\ne\n'

        with patch('jenkins_mcp.registrations.build.tools.build.get_build_console_output') as mock_tool:
            mock_tool.return_value = 'c\nd\n'
            func = mcp.tool.return_value.call_args_list[1][0][0]
            import asyncio
            result = asyncio.run(func('test', 42, offset=2, limit=2))
            assert result == 'c\nd\n'
