import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture
def jk():
    return MagicMock()


class TestGetAllConfigHistory:
    async def test_default_filter(self, jk):
        jk.run_script.return_value = '[]'
        from jenkins_mcp.tools.plugins_management.job_config_history import get_all_config_history
        result = await get_all_config_history(jk)
        assert isinstance(result, list)

    async def test_with_filter(self, jk):
        jk.run_script.return_value = '[]'
        from jenkins_mcp.tools.plugins_management.job_config_history import get_all_config_history
        result = await get_all_config_history(jk, filter_param='system')
        assert isinstance(result, list)


class TestGetJobConfigHistory:
    async def test_basic(self, jk):
        jk.run_script.return_value = '[]'
        from jenkins_mcp.tools.plugins_management.job_config_history import get_job_config_history
        result = await get_job_config_history(jk, 'test')
        assert isinstance(result, list)


class TestGetNodeConfigHistory:
    async def test_basic(self, jk):
        jk.run_script.return_value = '[]'
        from jenkins_mcp.tools.plugins_management.job_config_history import get_node_config_history
        result = await get_node_config_history(jk, 'agent1')
        assert isinstance(result, list)


class TestGetConfigFileContent:
    async def test_basic(self, jk):
        jk.run_script.return_value = '{"content": "<xml/>", "timestamp": "2024-01-15_10-30-00"}'
        from jenkins_mcp.tools.plugins_management.job_config_history import get_config_file_content
        result = await get_config_file_content(jk, 'test', '2024-01-15_10-30-00')
        assert result['content'] == '<xml/>'

    async def test_not_found(self, jk):
        jk.run_script.return_value = 'null'
        from jenkins_mcp.tools.plugins_management.job_config_history import get_config_file_content
        result = await get_config_file_content(jk, 'test', '2024-01-15_10-30-00')
        assert result is None


class TestRestoreJobConfig:
    async def test_restores(self, jk):
        jk.run_script.return_value = 'true'
        from jenkins_mcp.tools.plugins_management.job_config_history import restore_job_config
        result = await restore_job_config(jk, 'test', '2024-01-15_10-30-00')
        assert result['status'] == 'restored'


class TestRestoreNodeConfig:
    async def test_restores(self, jk):
        jk.run_script.return_value = 'true'
        from jenkins_mcp.tools.plugins_management.job_config_history import restore_node_config
        result = await restore_node_config(jk, 'agent1', '2024-01-15_10-30-00')
        assert result['status'] == 'restored'


class TestDeleteJobConfigRevision:
    async def test_deletes(self, jk):
        jk.run_script.return_value = 'true'
        from jenkins_mcp.tools.plugins_management.job_config_history import delete_job_config_revision
        result = await delete_job_config_revision(jk, 'test', '2024-01-15_10-30-00')
        assert result['status'] == 'deleted'


class TestDeleteNodeConfigRevision:
    async def test_deletes(self, jk):
        jk.run_script.return_value = 'true'
        from jenkins_mcp.tools.plugins_management.job_config_history import delete_node_config_revision
        result = await delete_node_config_revision(jk, 'agent1', '2024-01-15_10-30-00')
        assert result['status'] == 'deleted'


class TestRestoreDeletedJob:
    async def test_restores(self, jk):
        jk.run_script.return_value = 'true'
        from jenkins_mcp.tools.plugins_management.job_config_history import restore_deleted_job
        result = await restore_deleted_job(jk, 'deleted_job')
        assert result['status'] == 'restored'


class TestGetConfigDiff:
    async def test_basic(self, jk):
        jk.run_script.return_value = '{"diff": "--- a\\n+++ b\\n"}'
        from jenkins_mcp.tools.plugins_management.job_config_history import get_config_diff
        result = await get_config_diff(jk, 'test', 'ts1', 'ts2')
        assert 'diff' in result
