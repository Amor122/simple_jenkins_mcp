import pytest
from unittest.mock import MagicMock


@pytest.fixture
def jk():
    return MagicMock()


class TestGetViews:
    async def test_basic(self, jk):
        jk.get_views.return_value = [{'name': 'All'}, {'name': 'MyView'}]
        from jenkins_mcp.tools.view import get_views
        result = await get_views(jk)
        assert len(result) == 2
        jk.get_views.assert_called_once()


class TestViewExists:
    async def test_true(self, jk):
        jk.view_exists.return_value = True
        from jenkins_mcp.tools.view import view_exists
        assert await view_exists(jk, 'All') is True

    async def test_false(self, jk):
        jk.view_exists.return_value = False
        from jenkins_mcp.tools.view import view_exists
        assert await view_exists(jk, 'NoView') is False


class TestGetViewName:
    async def test_basic(self, jk):
        jk.get_view_name.return_value = 'All'
        from jenkins_mcp.tools.view import get_view_name
        result = await get_view_name(jk, 'All')
        assert result == 'All'


class TestGetViewConfig:
    async def test_basic(self, jk):
        jk.get_view_config.return_value = '<xml/>'
        from jenkins_mcp.tools.view import get_view_config
        result = await get_view_config(jk, 'All')
        assert result == '<xml/>'


class TestCreateView:
    async def test_creates(self, jk):
        from jenkins_mcp.tools.view import create_view
        result = await create_view(jk, 'NewView', '<view/>')
        jk.create_view.assert_called_once_with('NewView', '<view/>')
        assert result['status'] == 'created'

    async def test_error(self, jk):
        from jenkins_mcp.jenkins import JenkinsException
        jk.create_view.side_effect = JenkinsException('exists')
        from jenkins_mcp.tools.view import create_view
        result = await create_view(jk, 'Dup', '<view/>')
        assert 'error' in result


class TestReconfigView:
    async def test_reconfigs(self, jk):
        from jenkins_mcp.tools.view import reconfig_view
        result = await reconfig_view(jk, 'MyView', '<new/>')
        jk.reconfig_view.assert_called_once_with('MyView', '<new/>')
        assert result['status'] == 'updated'


class TestDeleteView:
    async def test_deletes(self, jk):
        from jenkins_mcp.tools.view import delete_view
        result = await delete_view(jk, 'MyView')
        jk.delete_view.assert_called_once_with('MyView')
        assert result['status'] == 'deleted'

    async def test_error(self, jk):
        from jenkins_mcp.jenkins import JenkinsException
        jk.delete_view.side_effect = JenkinsException('fail')
        from jenkins_mcp.tools.view import delete_view
        result = await delete_view(jk, 'MyView')
        assert 'error' in result
