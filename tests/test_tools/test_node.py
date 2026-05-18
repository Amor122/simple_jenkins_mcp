import pytest
from unittest.mock import MagicMock


@pytest.fixture
def jk():
    return MagicMock()


class TestGetAllNodes:
    async def test_basic(self, jk):
        jk.get_nodes.return_value = [{'displayName': 'master'}]
        from jenkins_mcp.tools.node import get_all_nodes
        result = await get_all_nodes(jk)
        assert len(result) == 1
        jk.get_nodes.assert_called_once_with(0)

    async def test_with_depth(self, jk):
        from jenkins_mcp.tools.node import get_all_nodes
        await get_all_nodes(jk, depth=2)
        jk.get_nodes.assert_called_once_with(2)


class TestGetNode:
    async def test_basic(self, jk):
        jk.get_node_info.return_value = {'displayName': 'agent1'}
        from jenkins_mcp.tools.node import get_node
        result = await get_node(jk, 'agent1')
        assert result['displayName'] == 'agent1'
        jk.get_node_info.assert_called_once_with('agent1', 2)


class TestGetNodeConfig:
    async def test_basic(self, jk):
        jk.get_node_config.return_value = '<xml/>'
        from jenkins_mcp.tools.node import get_node_config
        result = await get_node_config(jk, 'agent1')
        assert result == '<xml/>'


class TestNodeExists:
    async def test_true(self, jk):
        jk.node_exists.return_value = True
        from jenkins_mcp.tools.node import node_exists
        assert await node_exists(jk, 'agent1') is True

    async def test_false(self, jk):
        jk.node_exists.return_value = False
        from jenkins_mcp.tools.node import node_exists
        assert await node_exists(jk, 'agent1') is False


class TestSetNodeConfig:
    async def test_sets(self, jk):
        from jenkins_mcp.tools.node import set_node_config
        result = await set_node_config(jk, 'agent1', '<new/>')
        jk.reconfig_node.assert_called_once_with('agent1', '<new/>')
        assert result['status'] == 'updated'

    async def test_error(self, jk):
        from jenkins_mcp.jenkins import JenkinsException
        jk.reconfig_node.side_effect = JenkinsException('fail')
        from jenkins_mcp.tools.node import set_node_config
        result = await set_node_config(jk, 'agent1', '<new/>')
        assert 'error' in result


class TestCreateNode:
    async def test_creates(self, jk):
        from jenkins_mcp.tools.node import create_node
        result = await create_node(jk, 'new_node', '<xml/>')
        jk.create_node.assert_called_once_with('new_node', config_xml='<xml/>')
        assert result['status'] == 'created'

    async def test_error(self, jk):
        from jenkins_mcp.jenkins import JenkinsException
        jk.create_node.side_effect = JenkinsException('fail')
        from jenkins_mcp.tools.node import create_node
        result = await create_node(jk, 'new_node', '<xml/>')
        assert 'error' in result


class TestDeleteNode:
    async def test_deletes(self, jk):
        from jenkins_mcp.tools.node import delete_node
        result = await delete_node(jk, 'agent1')
        jk.delete_node.assert_called_once_with('agent1')
        assert result['status'] == 'deleted'

    async def test_error(self, jk):
        from jenkins_mcp.jenkins import JenkinsException
        jk.delete_node.side_effect = JenkinsException('fail')
        from jenkins_mcp.tools.node import delete_node
        result = await delete_node(jk, 'agent1')
        assert 'error' in result


class TestSetNodeOffline:
    async def test_offline(self, jk):
        from jenkins_mcp.tools.node import set_node_offline
        result = await set_node_offline(jk, 'agent1', message='maintenance')
        jk.disable_node.assert_called_once_with('agent1', 'maintenance')
        assert result['status'] == 'offline'

    async def test_no_msg(self, jk):
        from jenkins_mcp.tools.node import set_node_offline
        await set_node_offline(jk, 'agent1')
        jk.disable_node.assert_called_once_with('agent1', '')


class TestSetNodeOnline:
    async def test_online(self, jk):
        from jenkins_mcp.tools.node import set_node_online
        result = await set_node_online(jk, 'agent1')
        jk.enable_node.assert_called_once_with('agent1')
        assert result['status'] == 'online'
