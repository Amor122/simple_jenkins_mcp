import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture
def jk():
    return MagicMock()


class TestGetGlobalProperties:
    async def test_basic(self, jk):
        jk.run_script.return_value = '[]'
        from jenkins_mcp.tools.plugins_management.global_properties import get_global_properties
        result = await get_global_properties(jk)
        assert isinstance(result, list)

    async def test_with_values(self, jk):
        jk.run_script.return_value = '[{"key": "VAR1", "value": "val1"}, {"key": "VAR2", "value": "val2"}]'
        from jenkins_mcp.tools.plugins_management.global_properties import get_global_properties
        result = await get_global_properties(jk)
        assert len(result) == 2
        assert result[0]['key'] == 'VAR1'


class TestSetGlobalProperty:
    async def test_no_confirm(self):
        from jenkins_mcp.tools.plugins_management.global_properties import set_global_property
        result = set_global_property('admin', 'token', 'KEY', 'val')
        assert 'confirm' in result

    async def test_confirm(self):
        from jenkins_mcp.tools.plugins_management.global_properties import set_global_property
        with patch('jenkins_mcp.tools.plugins_management.global_properties.create_jenkins_client') as mock_cj:
            mock_client = MagicMock()
            mock_client.run_script.return_value = 'true'
            mock_cj.return_value = mock_client
            result = set_global_property('admin', 'token', 'KEY', 'val', confirm=True)
            assert result['status'] == 'set'


class TestDeleteGlobalProperty:
    async def test_no_confirm(self):
        from jenkins_mcp.tools.plugins_management.global_properties import delete_global_property
        result = delete_global_property('admin', 'token', 'KEY')
        assert 'confirm' in result

    async def test_confirm(self):
        from jenkins_mcp.tools.plugins_management.global_properties import delete_global_property
        with patch('jenkins_mcp.tools.plugins_management.global_properties.create_jenkins_client') as mock_cj:
            mock_client = MagicMock()
            mock_client.run_script.return_value = 'true'
            mock_cj.return_value = mock_client
            result = delete_global_property('admin', 'token', 'KEY', confirm=True)
            assert result['status'] == 'deleted'
