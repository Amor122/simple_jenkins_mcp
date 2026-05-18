import pytest
from unittest.mock import MagicMock


@pytest.fixture
def jk():
    return MagicMock()


class TestGetAllClouds:
    async def test_basic(self, jk):
        jk.get_info.return_value = {
            'primaryView': {'name': 'All'},
            'views': [{'name': 'All'}],
            'assignedLabels': [{'name': 'master'}],
            'description': 'jenkins',
        }
        from jenkins_mcp.tools.cloud import get_all_clouds
        result = await get_all_clouds(jk)
        assert isinstance(result, list)

    async def test_no_clouds(self, jk):
        jk.get_info.return_value = {}
        from jenkins_mcp.tools.cloud import get_all_clouds
        result = await get_all_clouds(jk)
        assert result == []


class TestGetCloudConfig:
    async def test_basic(self, jk):
        jk.get_info.return_value = {}
        from jenkins_mcp.tools.cloud import get_cloud_config
        result = await get_cloud_config(jk, 'docker')
        assert isinstance(result, dict)


class TestGetCloudTemplates:
    async def test_basic(self, jk):
        from jenkins_mcp.tools.cloud import get_cloud_templates
        result = await get_cloud_templates(jk, 'docker')
        assert isinstance(result, list)


class TestAnalyzeCloudNodes:
    async def test_basic(self, jk):
        from jenkins_mcp.tools.cloud import analyze_cloud_nodes
        result = await analyze_cloud_nodes(jk)
        assert isinstance(result, dict)


class TestGetCloudsByType:
    async def test_basic(self, jk):
        from jenkins_mcp.tools.cloud import get_clouds_by_type
        result = await get_clouds_by_type(jk)
        assert isinstance(result, list)


class TestGetKubernetesPods:
    async def test_basic(self, jk):
        from jenkins_mcp.tools.cloud import get_kubernetes_pods
        result = await get_kubernetes_pods(jk)
        assert isinstance(result, dict)

    async def test_with_namespace(self, jk):
        from jenkins_mcp.tools.cloud import get_kubernetes_pods
        await get_kubernetes_pods(jk, namespace='jenkins')
        jk.run_script.assert_called_once()


class TestUpdateCloudConfig:
    async def test_updates(self, jk):
        from jenkins_mcp.tools.cloud import update_cloud_config
        result = await update_cloud_config(jk, 'docker', {'key': 'val'})
        assert result['status'] == 'updated'


class TestDisableCloud:
    async def test_disables(self, jk):
        from jenkins_mcp.tools.cloud import disable_cloud
        result = await disable_cloud(jk, 'docker')
        assert result['status'] == 'disabled'


class TestEnableCloud:
    async def test_enables(self, jk):
        from jenkins_mcp.tools.cloud import enable_cloud
        result = await enable_cloud(jk, 'docker')
        assert result['status'] == 'enabled'


class TestDeleteCloud:
    async def test_deletes(self, jk):
        from jenkins_mcp.tools.cloud import delete_cloud
        result = await delete_cloud(jk, 'docker')
        assert result['status'] == 'deleted'


class TestDeleteTemplate:
    async def test_deletes(self, jk):
        from jenkins_mcp.tools.cloud import delete_template
        result = await delete_template(jk, 'docker', 'template1')
        assert result['status'] == 'deleted'


class TestCreateKubernetesCloud:
    async def test_creates(self, jk):
        from jenkins_mcp.tools.cloud import create_kubernetes_cloud
        result = await create_kubernetes_cloud(jk, 'k8s', 'https://k8s:8443')
        assert result['status'] == 'created'


class TestAddPodTemplate:
    async def test_adds(self, jk):
        from jenkins_mcp.tools.cloud import add_pod_template
        result = await add_pod_template(jk, 'k8s', {'name': 'pod1', 'containers': []})
        assert result['status'] == 'added'


class TestGetProvisioningStats:
    async def test_basic(self, jk):
        from jenkins_mcp.tools.cloud import get_provisioning_stats
        result = await get_provisioning_stats(jk)
        assert isinstance(result, dict)
