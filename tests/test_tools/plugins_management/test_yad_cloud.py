import pytest
from unittest.mock import MagicMock


@pytest.fixture
def jk():
    return MagicMock()


class TestGetYadClouds:
    async def test_basic(self, jk):
        jk.run_script.return_value = '[]'
        from jenkins_mcp.tools.plugins_management.yad_cloud import get_yad_clouds
        result = await get_yad_clouds(jk)
        assert isinstance(result, list)


class TestGetYadCloud:
    async def test_found(self, jk):
        jk.run_script.return_value = '{"name": "yad1", "serverUrl": "http://yad:8080"}'
        from jenkins_mcp.tools.plugins_management.yad_cloud import get_yad_cloud
        result = await get_yad_cloud(jk, 'yad1')
        assert result['name'] == 'yad1'

    async def test_not_found(self, jk):
        jk.run_script.return_value = 'null'
        from jenkins_mcp.tools.plugins_management.yad_cloud import get_yad_cloud
        result = await get_yad_cloud(jk, 'nonexistent')
        assert result is None


class TestCreateYadCloud:
    async def test_creates(self, jk):
        jk.run_script.return_value = 'true'
        from jenkins_mcp.tools.plugins_management.yad_cloud import create_yad_cloud
        result = await create_yad_cloud(jk, 'yad1', 'http://yad:8080')
        assert result['status'] == 'created'


class TestDeleteYadCloud:
    async def test_deletes(self, jk):
        jk.run_script.return_value = 'true'
        from jenkins_mcp.tools.plugins_management.yad_cloud import delete_yad_cloud
        result = await delete_yad_cloud(jk, 'yad1')
        assert result['status'] == 'deleted'


class TestGetYadTemplates:
    async def test_basic(self, jk):
        jk.run_script.return_value = '[]'
        from jenkins_mcp.tools.plugins_management.yad_cloud import get_yad_templates
        result = await get_yad_templates(jk, 'yad1')
        assert isinstance(result, list)


class TestGetYadTemplate:
    async def test_found(self, jk):
        jk.run_script.return_value = '{"id": "t1", "image": "node:latest"}'
        from jenkins_mcp.tools.plugins_management.yad_cloud import get_yad_template
        result = await get_yad_template(jk, 'yad1', 't1')
        assert result['id'] == 't1'

    async def test_not_found(self, jk):
        jk.run_script.return_value = 'null'
        from jenkins_mcp.tools.plugins_management.yad_cloud import get_yad_template
        result = await get_yad_template(jk, 'yad1', 'nonexistent')
        assert result is None


class TestAddYadTemplate:
    async def test_adds(self, jk):
        jk.run_script.return_value = 'true'
        from jenkins_mcp.tools.plugins_management.yad_cloud import add_yad_template
        result = await add_yad_template(jk, 'yad1', {'image': 'node:latest'})
        assert result['status'] == 'created'


class TestUpdateYadTemplate:
    async def test_updates(self, jk):
        jk.run_script.return_value = 'true'
        from jenkins_mcp.tools.plugins_management.yad_cloud import update_yad_template
        result = await update_yad_template(jk, 'yad1', 't1', {'image': 'node:18'})
        assert result['status'] == 'updated'


class TestDeleteYadTemplate:
    async def test_deletes(self, jk):
        jk.run_script.return_value = 'true'
        from jenkins_mcp.tools.plugins_management.yad_cloud import delete_yad_template
        result = await delete_yad_template(jk, 'yad1', 't1')
        assert result['status'] == 'deleted'


class TestCopyYadTemplate:
    async def test_copies(self, jk):
        jk.run_script.return_value = 'true'
        from jenkins_mcp.tools.plugins_management.yad_cloud import copy_yad_template
        result = await copy_yad_template(jk, 'yad1', 't1', 't2')
        assert result['status'] == 'copied'
