import pytest
from unittest.mock import MagicMock


@pytest.fixture
def jk():
    return MagicMock()


class TestGetAllQueueItems:
    async def test_basic(self, jk):
        jk.get_queue_info.return_value = [{'id': 1}, {'id': 2}]
        from jenkins_mcp.tools.queue import get_all_queue_items
        result = await get_all_queue_items(jk)
        assert len(result) == 2


class TestGetQueueItem:
    async def test_basic(self, jk):
        jk.get_queue_item.return_value = {'id': 1, 'task': {'name': 'test'}}
        from jenkins_mcp.tools.queue import get_queue_item
        result = await get_queue_item(jk, 1)
        assert result['id'] == 1
        jk.get_queue_item.assert_called_once_with(1, 0)

    async def test_with_depth(self, jk):
        from jenkins_mcp.tools.queue import get_queue_item
        await get_queue_item(jk, 1, depth=2)
        jk.get_queue_item.assert_called_once_with(1, 2)


class TestGetQueueItemsByJob:
    async def test_basic(self, jk):
        jk.get_queue_info.return_value = [
            {'id': 1, 'task': {'name': 'myjob'}},
            {'id': 2, 'task': {'name': 'other'}},
            {'id': 3, 'task': {'name': 'myjob'}},
        ]
        from jenkins_mcp.tools.queue import get_queue_items_by_job
        result = await get_queue_items_by_job(jk, 'myjob')
        assert len(result) == 2

    async def test_none(self, jk):
        jk.get_queue_info.return_value = []
        from jenkins_mcp.tools.queue import get_queue_items_by_job
        result = await get_queue_items_by_job(jk, 'myjob')
        assert result == []


class TestCancelQueueItem:
    async def test_cancels(self, jk):
        from jenkins_mcp.tools.queue import cancel_queue_item
        result = await cancel_queue_item(jk, 42)
        jk.cancel_queue.assert_called_once_with(42)
        assert result['status'] == 'cancelled'


class TestCancelJobQueue:
    async def test_cancels(self, jk):
        jk.get_queue_info.return_value = [
            {'id': 1, 'task': {'name': 'myjob'}},
            {'id': 2, 'task': {'name': 'other'}},
        ]
        from jenkins_mcp.tools.queue import cancel_job_queue
        result = await cancel_job_queue(jk, 'myjob')
        jk.cancel_queue.assert_called_once_with(1)
        assert result['cancelled'] == 1

    async def test_no_items(self, jk):
        jk.get_queue_info.return_value = []
        from jenkins_mcp.tools.queue import cancel_job_queue
        result = await cancel_job_queue(jk, 'myjob')
        assert result['cancelled'] == 0


class TestCancelAllQueue:
    async def test_cancels_all(self, jk):
        jk.get_queue_info.return_value = [{'id': 1}, {'id': 2}, {'id': 3}]
        from jenkins_mcp.tools.queue import cancel_all_queue
        result = await cancel_all_queue(jk)
        assert jk.cancel_queue.call_count == 3
        assert result['cancelled'] == 3

    async def test_empty(self, jk):
        jk.get_queue_info.return_value = []
        from jenkins_mcp.tools.queue import cancel_all_queue
        result = await cancel_all_queue(jk)
        assert result['cancelled'] == 0
