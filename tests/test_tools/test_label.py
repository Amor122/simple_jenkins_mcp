import pytest
from unittest.mock import MagicMock


@pytest.fixture
def jk():
    return MagicMock()


class TestGetAllLabels:
    async def test_basic(self, jk):
        jk.get_nodes.return_value = [
            {'displayName': 'master', 'labelName': ['built-in', 'master']},
            {'displayName': 'agent1', 'labelName': ['linux', 'docker']},
        ]
        from jenkins_mcp.tools.label import get_all_labels
        result = await get_all_labels(jk)
        assert 'linux' in result
        assert 'docker' in result
        assert 'master' in result
        jk.get_nodes.assert_called_once()


class TestGetLabel:
    async def test_basic(self, jk):
        jk.get_nodes.return_value = [
            {'displayName': 'agent1', 'labelName': ['linux', 'docker'], 'offline': False,
             'numExecutors': 2, 'idle': True},
        ]
        from jenkins_mcp.tools.label import get_label
        result = await get_label(jk, 'linux')
        assert result['name'] == 'linux'
        assert len(result['nodes']) == 1
        assert result['nodes'][0]['displayName'] == 'agent1'

    async def test_not_found(self, jk):
        jk.get_nodes.return_value = []
        from jenkins_mcp.tools.label import get_label
        result = await get_label(jk, 'nonexistent')
        assert 'error' in result


class TestGetNodesByLabel:
    async def test_basic(self, jk):
        jk.get_nodes.return_value = [
            {'displayName': 'agent1', 'labelName': ['linux'], 'offline': False,
             'numExecutors': 2, 'idle': True},
            {'displayName': 'agent2', 'labelName': ['windows'], 'offline': False,
             'numExecutors': 2, 'idle': True},
        ]
        from jenkins_mcp.tools.label import get_nodes_by_label
        result = await get_nodes_by_label(jk, 'linux')
        assert len(result) == 1
        assert result[0]['displayName'] == 'agent1'

    async def test_no_match(self, jk):
        jk.get_nodes.return_value = []
        from jenkins_mcp.tools.label import get_nodes_by_label
        result = await get_nodes_by_label(jk, 'nonexistent')
        assert result == []


class TestGetLabelLoad:
    async def test_basic(self, jk):
        jk.get_nodes.return_value = [
            {'displayName': 'master', 'labelName': ['built-in'], 'numExecutors': 2, 'idle': True},
            {'displayName': 'agent1', 'labelName': ['linux'], 'numExecutors': 4, 'idle': False},
        ]
        from jenkins_mcp.tools.label import get_label_load
        result = await get_label_load(jk)
        assert 'built-in' in result
        assert 'linux' in result
        assert result['linux']['total'] == 4
