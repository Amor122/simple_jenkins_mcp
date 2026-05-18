import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture
def jk():
    return MagicMock()


class TestGetAllConfigFiles:
    async def test_basic(self, jk):
        jk.run_script.return_value = '[]'
        from jenkins_mcp.tools.plugins_management.config_file_provider import get_all_config_files
        result = await get_all_config_files(jk)
        assert isinstance(result, list)


class TestGetConfigFile:
    async def test_found(self, jk):
        jk.run_script.return_value = '{"id": "cfg1", "name": "my-config"}'
        from jenkins_mcp.tools.plugins_management.config_file_provider import get_config_file
        result = await get_config_file(jk, 'cfg1')
        assert result['id'] == 'cfg1'

    async def test_not_found(self, jk):
        jk.run_script.return_value = 'null'
        from jenkins_mcp.tools.plugins_management.config_file_provider import get_config_file
        result = await get_config_file(jk, 'nonexistent')
        assert result is None


class TestAddConfigFile:
    async def test_adds(self, jk):
        jk.run_script.return_value = 'true'
        from jenkins_mcp.tools.plugins_management.config_file_provider import add_config_file
        result = await add_config_file(jk, 'my-config', 'content here')
        assert result['status'] == 'created'
        assert result['name'] == 'my-config'


class TestUpdateConfigFile:
    async def test_updates(self, jk):
        jk.run_script.return_value = 'true'
        from jenkins_mcp.tools.plugins_management.config_file_provider import update_config_file
        result = await update_config_file(jk, 'cfg1', 'new-name', 'new content')
        assert result['status'] == 'updated'


class TestDeleteConfigFile:
    async def test_deletes(self, jk):
        jk.run_script.return_value = 'true'
        from jenkins_mcp.tools.plugins_management.config_file_provider import delete_config_file
        result = await delete_config_file(jk, 'cfg1')
        assert result['status'] == 'deleted'


class TestGetAllConfigProviders:
    async def test_basic(self, jk):
        jk.run_script.return_value = '[]'
        from jenkins_mcp.tools.plugins_management.config_file_provider import get_all_config_providers
        result = await get_all_config_providers(jk)
        assert isinstance(result, list)


class TestGetConfigFilesByProvider:
    async def test_basic(self, jk):
        jk.run_script.return_value = '[]'
        from jenkins_mcp.tools.plugins_management.config_file_provider import get_config_files_by_provider
        result = await get_config_files_by_provider(jk, 'some-provider')
        assert isinstance(result, list)
