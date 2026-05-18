import pytest
from unittest.mock import MagicMock


@pytest.fixture
def jk():
    return MagicMock()


class TestGetJobDownstreamProjects:
    async def test_basic(self, jk):
        jk.run_script.return_value = '[]'
        from jenkins_mcp.tools.plugins_management.downstream_buildview import get_job_downstream_projects
        result = await get_job_downstream_projects(jk, 'test')
        assert isinstance(result, list)

    async def test_with_results(self, jk):
        jk.run_script.return_value = '[{"name": "downstream_job", "url": "http://jenkins:8080/job/downstream_job/"}]'
        from jenkins_mcp.tools.plugins_management.downstream_buildview import get_job_downstream_projects
        result = await get_job_downstream_projects(jk, 'test')
        assert len(result) == 1
        assert result[0]['name'] == 'downstream_job'


class TestGetJobUpstreamProjects:
    async def test_basic(self, jk):
        jk.run_script.return_value = '[]'
        from jenkins_mcp.tools.plugins_management.downstream_buildview import get_job_upstream_projects
        result = await get_job_upstream_projects(jk, 'test')
        assert isinstance(result, list)


class TestGetBuildDownstream:
    async def test_basic(self, jk):
        jk.run_script.return_value = '[]'
        from jenkins_mcp.tools.plugins_management.downstream_buildview import get_build_downstream
        result = await get_build_downstream(jk, 'test', 42)
        assert isinstance(result, list)

    async def test_with_results(self, jk):
        jk.run_script.return_value = '[{"job_name": "downstream", "build_number": 1, "url": "http://jenkins:8080/job/downstream/1/"}]'
        from jenkins_mcp.tools.plugins_management.downstream_buildview import get_build_downstream
        result = await get_build_downstream(jk, 'test', 42)
        assert len(result) == 1
        assert result[0]['job_name'] == 'downstream'


class TestGetBuildUpstream:
    async def test_with_upstream(self, jk):
        jk.run_script.return_value = '{"job_name": "parent", "build_number": 10, "url": "http://jenkins:8080/job/parent/10/"}'
        from jenkins_mcp.tools.plugins_management.downstream_buildview import get_build_upstream
        result = await get_build_upstream(jk, 'test', 42)
        assert result['job_name'] == 'parent'

    async def test_no_upstream(self, jk):
        jk.run_script.return_value = '{}'
        from jenkins_mcp.tools.plugins_management.downstream_buildview import get_build_upstream
        result = await get_build_upstream(jk, 'test', 42)
        assert result is None


class TestGetBuildDownstreamTree:
    async def test_basic(self, jk):
        jk.run_script.return_value = '[]'
        from jenkins_mcp.tools.plugins_management.downstream_buildview import get_build_downstream_tree
        result = await get_build_downstream_tree(jk, 'test', 42)
        assert isinstance(result, dict)
        assert result['job_name'] == 'test'

    async def test_with_tree(self, jk):
        jk.run_script.return_value = '[{"job_name": "child", "build_number": 1}]'
        from jenkins_mcp.tools.plugins_management.downstream_buildview import get_build_downstream_tree
        result = await get_build_downstream_tree(jk, 'test', 42)
        assert len(result.get('downstream', [])) == 1


class TestGetBuildUpstreamChain:
    async def test_basic(self, jk):
        jk.run_script.return_value = '{}'
        from jenkins_mcp.tools.plugins_management.downstream_buildview import get_build_upstream_chain
        result = await get_build_upstream_chain(jk, 'test', 42)
        assert isinstance(result, dict)
        assert result['job_name'] == 'test'
