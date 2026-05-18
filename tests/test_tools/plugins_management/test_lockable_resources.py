import pytest
from unittest.mock import MagicMock


@pytest.fixture
def jk():
    return MagicMock()


class MockResponse:
    def __init__(self, status=200, text='{}', json_data=None):
        self.status_code = status
        self.text = text
        self._json = json_data
        self.reason = 'OK'

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f'HTTP {self.status_code}')

    def json(self):
        return self._json or {}


class TestGetAllLockableResources:
    async def test_basic(self, jk):
        jk.run_script.return_value = '[]'
        from jenkins_mcp.tools.plugins_management.lockable_resources import get_all_lockable_resources
        result = await get_all_lockable_resources(jk)
        assert isinstance(result, list)


class TestGetLockableResource:
    async def test_found(self, jk):
        jk.run_script.return_value = '[{"name": "res1", "labels": [], "locked": false}]'
        from jenkins_mcp.tools.plugins_management.lockable_resources import get_lockable_resource
        result = await get_lockable_resource(jk, 'res1')
        assert result['name'] == 'res1'

    async def test_not_found(self, jk):
        jk.run_script.return_value = '[]'
        from jenkins_mcp.tools.plugins_management.lockable_resources import get_lockable_resource
        result = await get_lockable_resource(jk, 'nonexistent')
        assert result is None


class TestLockableResourceExists:
    async def test_true(self, jk):
        jk.run_script.return_value = '[{"name": "res1"}]'
        from jenkins_mcp.tools.plugins_management.lockable_resources import lockable_resource_exists
        assert await lockable_resource_exists(jk, 'res1') is True

    async def test_false(self, jk):
        jk.run_script.return_value = '[]'
        from jenkins_mcp.tools.plugins_management.lockable_resources import lockable_resource_exists
        assert await lockable_resource_exists(jk, 'res1') is False


class TestReserveLockableResource:
    async def test_reserves(self, jk):
        jk.run_script.return_value = 'true'
        from jenkins_mcp.tools.plugins_management.lockable_resources import reserve_lockable_resource
        result = await reserve_lockable_resource(jk, 'res1', user='admin', reason='testing')
        assert result['status'] == 'reserved'


class TestUnreserveLockableResource:
    async def test_unreserves(self, jk):
        jk.run_script.return_value = 'true'
        from jenkins_mcp.tools.plugins_management.lockable_resources import unreserve_lockable_resource
        result = await unreserve_lockable_resource(jk, 'res1')
        assert result['status'] == 'unreserved'


class TestGetLockableQueue:
    async def test_basic(self, jk):
        jk.run_script.return_value = '[]'
        from jenkins_mcp.tools.plugins_management.lockable_resources import get_lockable_queue
        result = await get_lockable_queue(jk)
        assert isinstance(result, list)


class TestGetAllLockableLabels:
    async def test_basic(self, jk):
        jk.run_script.return_value = '[]'
        from jenkins_mcp.tools.plugins_management.lockable_resources import get_all_lockable_labels
        result = await get_all_lockable_labels(jk)
        assert isinstance(result, list)


class TestGetLockableResourcesByLabel:
    async def test_basic(self, jk):
        jk.run_script.return_value = '[]'
        from jenkins_mcp.tools.plugins_management.lockable_resources import get_lockable_resources_by_label
        result = await get_lockable_resources_by_label(jk, 'label1')
        assert isinstance(result, list)


class TestAddLockableResource:
    async def test_adds(self, jk):
        from unittest.mock import patch
        import json

        with patch('jenkins_mcp.tools.plugins_management.lockable_resources.requests') as mock_requests:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_requests.post.return_value = mock_response

            from jenkins_mcp.tools.plugins_management.lockable_resources import add_lockable_resource
            result = await add_lockable_resource(jk, 'res1', labels='l1 l2')
            assert result['status'] == 'created'


class TestDeleteLockableResource:
    async def test_deletes(self, jk):
        from unittest.mock import patch
        with patch('jenkins_mcp.tools.plugins_management.lockable_resources.requests') as mock_requests:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_requests.post.return_value = mock_response

            from jenkins_mcp.tools.plugins_management.lockable_resources import delete_lockable_resource
            result = await delete_lockable_resource(jk, 'res1')
            assert result['status'] == 'deleted'


class TestSecureOperations:
    async def test_add_secure_no_confirm(self):
        from jenkins_mcp.tools.plugins_management.lockable_resources import add_lockable_resource_secure
        result = add_lockable_resource_secure('admin', 'token', 'res1')
        assert 'confirm' in result

    async def test_delete_secure_no_confirm(self):
        from jenkins_mcp.tools.plugins_management.lockable_resources import delete_lockable_resource_secure
        result = delete_lockable_resource_secure('admin', 'token', 'res1')
        assert 'confirm' in result

    async def test_unlock_secure_no_confirm(self):
        from jenkins_mcp.tools.plugins_management.lockable_resources import unlock_lockable_resource_secure
        result = unlock_lockable_resource_secure('admin', 'token', 'res1')
        assert 'confirm' in result


class TestSetLockableResourceProperties:
    async def test_set_properties(self, jk):
        from unittest.mock import patch
        with patch('jenkins_mcp.tools.plugins_management.lockable_resources.requests') as mock_requests:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_requests.post.return_value = mock_response

            from jenkins_mcp.tools.plugins_management.lockable_resources import set_lockable_resource_properties
            result = await set_lockable_resource_properties(jk, 'res1', {'key': 'val'})
            assert result['status'] == 'updated'

    async def test_set_property(self, jk):
        from unittest.mock import patch
        with patch('jenkins_mcp.tools.plugins_management.lockable_resources.requests') as mock_requests:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_requests.post.return_value = mock_response

            from jenkins_mcp.tools.plugins_management.lockable_resources import set_lockable_resource_property
            result = await set_lockable_resource_property(jk, 'res1', 'key', 'val')
            assert result['status'] == 'updated'

    async def test_get_property(self, jk):
        jk.run_script.return_value = '{"key": "val"}'
        from jenkins_mcp.tools.plugins_management.lockable_resources import get_lockable_resource_property
        result = await get_lockable_resource_property(jk, 'res1', 'key')
        assert result == 'val'

    async def test_get_property_not_found(self, jk):
        jk.run_script.return_value = '{"other_key": "val"}'
        from jenkins_mcp.tools.plugins_management.lockable_resources import get_lockable_resource_property
        result = await get_lockable_resource_property(jk, 'res1', 'key')
        assert result is None
