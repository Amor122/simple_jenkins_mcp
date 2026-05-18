import pytest
from unittest.mock import MagicMock


@pytest.fixture
def jk():
    return MagicMock()


class TestGetKubernetesClouds:
    async def test_basic(self, jk):
        jk.run_script.return_value = '[]'
        from jenkins_mcp.tools.plugins_management.kubernetes_cloud import get_kubernetes_clouds
        result = await get_kubernetes_clouds(jk)
        assert isinstance(result, list)


class TestGetKubernetesCloud:
    async def test_found(self, jk):
        jk.run_script.return_value = '{"name": "k8s1", "serverUrl": "https://k8s:8443"}'
        from jenkins_mcp.tools.plugins_management.kubernetes_cloud import get_kubernetes_cloud
        result = await get_kubernetes_cloud(jk, 'k8s1')
        assert result['name'] == 'k8s1'

    async def test_not_found(self, jk):
        jk.run_script.return_value = 'null'
        from jenkins_mcp.tools.plugins_management.kubernetes_cloud import get_kubernetes_cloud
        result = await get_kubernetes_cloud(jk, 'nonexistent')
        assert result is None


class TestCreateKubernetesCloud:
    async def test_creates(self, jk):
        jk.run_script.return_value = 'true'
        from jenkins_mcp.tools.plugins_management.kubernetes_cloud import create_kubernetes_cloud
        result = await create_kubernetes_cloud(jk, 'k8s1', 'https://k8s:8443')
        assert result['status'] == 'created'


class TestDeleteKubernetesCloud:
    async def test_deletes(self, jk):
        jk.run_script.return_value = 'true'
        from jenkins_mcp.tools.plugins_management.kubernetes_cloud import delete_kubernetes_cloud
        result = await delete_kubernetes_cloud(jk, 'k8s1')
        assert result['status'] == 'deleted'


class TestGetPodTemplates:
    async def test_basic(self, jk):
        jk.run_script.return_value = '[]'
        from jenkins_mcp.tools.plugins_management.kubernetes_cloud import get_pod_templates
        result = await get_pod_templates(jk, 'k8s1')
        assert isinstance(result, list)


class TestGetPodTemplate:
    async def test_found(self, jk):
        jk.run_script.return_value = '{"name": "pod1", "containers": []}'
        from jenkins_mcp.tools.plugins_management.kubernetes_cloud import get_pod_template
        result = await get_pod_template(jk, 'k8s1', 'pod1')
        assert result['name'] == 'pod1'

    async def test_not_found(self, jk):
        jk.run_script.return_value = 'null'
        from jenkins_mcp.tools.plugins_management.kubernetes_cloud import get_pod_template
        result = await get_pod_template(jk, 'k8s1', 'nonexistent')
        assert result is None


class TestAddPodTemplate:
    async def test_adds(self, jk):
        jk.run_script.return_value = 'true'
        from jenkins_mcp.tools.plugins_management.kubernetes_cloud import add_pod_template
        result = await add_pod_template(jk, 'k8s1', {'name': 'pod1', 'containers': []})
        assert result['status'] == 'created'


class TestUpdatePodTemplate:
    async def test_updates(self, jk):
        jk.run_script.return_value = 'true'
        from jenkins_mcp.tools.plugins_management.kubernetes_cloud import update_pod_template
        result = await update_pod_template(jk, 'k8s1', 'pod1', {'containers': [{'name': 'jnlp'}]})
        assert result['status'] == 'updated'


class TestDeletePodTemplate:
    async def test_deletes(self, jk):
        jk.run_script.return_value = 'true'
        from jenkins_mcp.tools.plugins_management.kubernetes_cloud import delete_pod_template
        result = await delete_pod_template(jk, 'k8s1', 'pod1')
        assert result['status'] == 'deleted'


class TestCopyPodTemplate:
    async def test_copies(self, jk):
        jk.run_script.return_value = 'true'
        from jenkins_mcp.tools.plugins_management.kubernetes_cloud import copy_pod_template
        result = await copy_pod_template(jk, 'k8s1', 'pod1', 'pod2')
        assert result['status'] == 'copied'
