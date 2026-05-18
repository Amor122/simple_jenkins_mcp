import pytest
from unittest.mock import MagicMock, patch


class TestRegisterResources:
    @pytest.fixture
    def mcp(self):
        return MagicMock()

    def test_registers_all_resources(self, mcp):
        from jenkins_mcp.registrations.resources import register_resources
        register_resources(mcp)
        assert mcp.resource.call_count == 7

    def test_jobs_resource(self, mcp):
        from jenkins_mcp.registrations.resources import register_resources
        register_resources(mcp)
        resource_calls = [c.args[0] if c.args else c.kwargs.get('uri') for c in mcp.resource.call_args_list]
        assert 'jenkins://jobs' in resource_calls
        assert 'jenkins://job/{name}/config' in resource_calls
        assert 'jenkins://job/{name}/build/{number}' in resource_calls
        assert 'jenkins://job/{name}/build/{number}/console' in resource_calls
        assert 'jenkins://system/version' in resource_calls
        assert 'jenkins://system/info' in resource_calls
        assert 'jenkins://queue' in resource_calls

    def test_debug_build_resource_returns_result(self, mcp):
        from jenkins_mcp.registrations.resources import register_resources
        register_resources(mcp)

        def get_jk():
            mock = MagicMock()
            mock.get_all_jobs.return_value = [{'name': 'test'}]
            return mock

        with patch('jenkins_mcp.server.get_jenkins_client', get_jk):
            func = None
            for i, call in enumerate(mcp.resource.call_args_list):
                if call.args and 'jenkins://jobs' in str(call.args[0]):
                    func = mcp.resource.return_value.call_args_list[i].args[0]
                    break
            if func:
                import asyncio
                result = asyncio.run(func())
                assert len(result) == 1
