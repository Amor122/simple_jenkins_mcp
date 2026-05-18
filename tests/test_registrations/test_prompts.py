import pytest
from unittest.mock import MagicMock, patch


class TestRegisterPrompts:
    @pytest.fixture
    def mcp(self):
        return MagicMock()

    def test_registers_all_prompts(self, mcp):
        from jenkins_mcp.registrations.prompts import register_prompts
        register_prompts(mcp)
        assert mcp.prompt.call_count == 3

    def test_debug_build_valid(self, mcp):
        from jenkins_mcp.registrations.prompts import register_prompts
        register_prompts(mcp)

        mock_jk = MagicMock()
        mock_jk.get_build_info.return_value = {'result': 'SUCCESS'}
        mock_jk.get_build_console_output.return_value = 'line1\nline2\n'
        mock_jk.get_build_env_vars.return_value = {'VAR': 'val'}

        with patch('jenkins_mcp.server.get_jenkins_client', return_value=mock_jk):
            func = mcp.prompt.return_value.call_args_list[0][0][0]
            import asyncio
            result = asyncio.run(func('test', '42'))
            assert 'SUCCESS' in result
            assert 'line1' in result
            assert 'VAR' in result

    def test_debug_build_invalid_build_number(self, mcp):
        from jenkins_mcp.registrations.prompts import register_prompts
        register_prompts(mcp)

        func = mcp.prompt.return_value.call_args_list[0][0][0]
        import asyncio
        result = asyncio.run(func('test', 'abc'))
        assert '无效的构建号' in result
        assert 'abc' in result

    def test_debug_build_dollar_variable(self, mcp):
        """Test that unexpanded client variables like $2 are gracefully handled"""
        from jenkins_mcp.registrations.prompts import register_prompts
        register_prompts(mcp)

        func = mcp.prompt.return_value.call_args_list[0][0][0]
        import asyncio
        result = asyncio.run(func('test', '$2'))
        assert '无效的构建号' in result
        assert '$2' in result

    def test_compare_builds_valid(self, mcp):
        from jenkins_mcp.registrations.prompts import register_prompts
        register_prompts(mcp)

        mock_jk = MagicMock()
        mock_jk.get_build_env_vars.side_effect = [
            {'A': '1', 'B': '2'},
            {'A': '1', 'B': '20', 'C': '3'},
        ]

        with patch('jenkins_mcp.server.get_jenkins_client', return_value=mock_jk):
            func = mcp.prompt.return_value.call_args_list[1][0][0]
            import asyncio
            result = asyncio.run(func('test', '1', '2'))
            assert 'Build #1 vs #2' in result or 'test' in result
            assert '新增' in result
            assert '移除' not in result

    def test_compare_builds_invalid(self, mcp):
        from jenkins_mcp.registrations.prompts import register_prompts
        register_prompts(mcp)

        func = mcp.prompt.return_value.call_args_list[1][0][0]
        import asyncio
        result = asyncio.run(func('test', 'abc', '2'))
        assert '无效的构建号' in result

    def test_compare_builds_dollar_variables(self, mcp):
        from jenkins_mcp.registrations.prompts import register_prompts
        register_prompts(mcp)

        func = mcp.prompt.return_value.call_args_list[1][0][0]
        import asyncio
        result = asyncio.run(func('test', '$1', '$2'))
        assert '无效的构建号' in result

    def test_safe_restart(self, mcp):
        from jenkins_mcp.registrations.prompts import register_prompts
        register_prompts(mcp)

        func = mcp.prompt.return_value.call_args_list[2][0][0]
        import asyncio
        result = asyncio.run(func())
        assert '安全重启' in result
