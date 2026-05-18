import pytest
from unittest.mock import MagicMock, patch


class TestRegisterJobTools:
    @pytest.fixture
    def mcp(self):
        return MagicMock()

    def test_registers_all_tools(self, mcp):
        from jenkins_mcp.registrations.job import register_tools
        register_tools(mcp)
        assert mcp.tool.call_count >= 7
        assert mcp.tool.call_count <= 14

    def test_get_job_calls_through(self, mcp):
        from jenkins_mcp.registrations.job import register_tools
        register_tools(mcp)

        mock_jk = MagicMock()
        mock_jk.get_job_info.return_value = {'name': 'test'}

        with patch('jenkins_mcp.registrations.job.tools.job.get_job') as mock_tool:
            mock_tool.return_value = {'name': 'test'}
            func = mcp.tool.return_value.call_args_list[0][0][0]
            import asyncio
            result = asyncio.run(func('test'))
            assert result['name'] == 'test'
