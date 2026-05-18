import pytest
from unittest.mock import MagicMock


@pytest.fixture
def jk():
    return MagicMock()


class TestGetDockerClouds:
    async def test_basic(self, jk):
        jk.run_script.return_value = '[]'
        from jenkins_mcp.tools.plugins_management.docker_cloud import get_docker_clouds
        result = await get_docker_clouds(jk)
        assert isinstance(result, list)


class TestGetDockerCloud:
    async def test_found(self, jk):
        jk.run_script.return_value = '{"name": "docker1", "serverUrl": "tcp://docker:2376"}'
        from jenkins_mcp.tools.plugins_management.docker_cloud import get_docker_cloud
        result = await get_docker_cloud(jk, 'docker1')
        assert result['name'] == 'docker1'

    async def test_not_found(self, jk):
        jk.run_script.return_value = 'null'
        from jenkins_mcp.tools.plugins_management.docker_cloud import get_docker_cloud
        result = await get_docker_cloud(jk, 'nonexistent')
        assert result is None


class TestCreateDockerCloud:
    async def test_creates(self, jk):
        jk.run_script.return_value = 'true'
        from jenkins_mcp.tools.plugins_management.docker_cloud import create_docker_cloud
        result = await create_docker_cloud(jk, 'docker1', 'tcp://docker:2376')
        assert result['status'] == 'created'


class TestDeleteDockerCloud:
    async def test_deletes(self, jk):
        jk.run_script.return_value = 'true'
        from jenkins_mcp.tools.plugins_management.docker_cloud import delete_docker_cloud
        result = await delete_docker_cloud(jk, 'docker1')
        assert result['status'] == 'deleted'


class TestGetDockerTemplates:
    async def test_basic(self, jk):
        jk.run_script.return_value = '[]'
        from jenkins_mcp.tools.plugins_management.docker_cloud import get_docker_templates
        result = await get_docker_templates(jk, 'docker1')
        assert isinstance(result, list)


class TestGetDockerTemplate:
    async def test_found(self, jk):
        jk.run_script.return_value = '{"name": "template1", "image": "node:latest"}'
        from jenkins_mcp.tools.plugins_management.docker_cloud import get_docker_template
        result = await get_docker_template(jk, 'docker1', 'template1')
        assert result['name'] == 'template1'

    async def test_not_found(self, jk):
        jk.run_script.return_value = 'null'
        from jenkins_mcp.tools.plugins_management.docker_cloud import get_docker_template
        result = await get_docker_template(jk, 'docker1', 'nonexistent')
        assert result is None


class TestAddDockerTemplate:
    async def test_adds(self, jk):
        jk.run_script.return_value = 'true'
        from jenkins_mcp.tools.plugins_management.docker_cloud import add_docker_template
        result = await add_docker_template(jk, 'docker1', {'name': 't1', 'image': 'node:latest'})
        assert result['status'] == 'created'


class TestUpdateDockerTemplate:
    async def test_updates(self, jk):
        jk.run_script.return_value = 'true'
        from jenkins_mcp.tools.plugins_management.docker_cloud import update_docker_template
        result = await update_docker_template(jk, 'docker1', 't1', {'image': 'node:18'})
        assert result['status'] == 'updated'


class TestDeleteDockerTemplate:
    async def test_deletes(self, jk):
        jk.run_script.return_value = 'true'
        from jenkins_mcp.tools.plugins_management.docker_cloud import delete_docker_template
        result = await delete_docker_template(jk, 'docker1', 't1')
        assert result['status'] == 'deleted'


class TestCopyDockerTemplate:
    async def test_copies(self, jk):
        jk.run_script.return_value = 'true'
        from jenkins_mcp.tools.plugins_management.docker_cloud import copy_docker_template
        result = await copy_docker_template(jk, 'docker1', 't1', 't2')
        assert result['status'] == 'copied'
