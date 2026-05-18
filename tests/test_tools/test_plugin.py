import pytest
from unittest.mock import MagicMock


@pytest.fixture
def jk():
    return MagicMock()


class TestGetAllPlugins:
    async def test_basic(self, jk):
        jk.get_plugins.return_value = [{'shortName': 'git'}]
        from jenkins_mcp.tools.plugin import get_all_plugins
        result = await get_all_plugins(jk)
        assert len(result) == 1
        jk.get_plugins.assert_called_once_with(2)

    async def test_with_depth(self, jk):
        from jenkins_mcp.tools.plugin import get_all_plugins
        await get_all_plugins(jk, depth=1)
        jk.get_plugins.assert_called_once_with(1)


class TestGetPlugin:
    async def test_found(self, jk):
        jk.get_plugin_info.return_value = {'shortName': 'git', 'version': '1.0'}
        from jenkins_mcp.tools.plugin import get_plugin
        result = await get_plugin(jk, 'git')
        assert result['shortName'] == 'git'
        jk.get_plugin_info.assert_called_once_with('git', 2)

    async def test_not_found(self, jk):
        jk.get_plugin_info.return_value = None
        from jenkins_mcp.tools.plugin import get_plugin
        result = await get_plugin(jk, 'nonexistent')
        assert 'error' in result


class TestGetPluginsWithProblems:
    async def test_basic(self, jk):
        jk.get_plugins.return_value = [
            {'shortName': 'good', 'hasUpdate': False},
            {'shortName': 'bad', 'hasUpdate': True, 'deleted': False},
        ]
        from jenkins_mcp.tools.plugin import get_plugins_with_problems
        result = await get_plugins_with_problems(jk)
        assert any(p['shortName'] == 'bad' for p in result)

    async def test_no_problems(self, jk):
        jk.get_plugins.return_value = [
            {'shortName': 'a', 'hasUpdate': False},
            {'shortName': 'b', 'hasUpdate': False},
        ]
        from jenkins_mcp.tools.plugin import get_plugins_with_problems
        result = await get_plugins_with_problems(jk)
        assert result == []


class TestInstallPlugin:
    async def test_installs(self, jk):
        jk.install_plugin.return_value = {'status': 'installed', 'plugin': 'git'}
        from jenkins_mcp.tools.plugin import install_plugin
        result = await install_plugin(jk, 'git')
        jk.install_plugin.assert_called_once_with('git', None)
        assert result['status'] == 'installed'

    async def test_with_version(self, jk):
        jk.install_plugin.return_value = {'status': 'installed', 'plugin': 'git', 'version': '2.0'}
        from jenkins_mcp.tools.plugin import install_plugin
        await install_plugin(jk, 'git', version='2.0')
        jk.install_plugin.assert_called_once_with('git', '2.0')


class TestEnablePlugin:
    async def test_enables(self, jk):
        from jenkins_mcp.tools.plugin import enable_plugin
        result = await enable_plugin(jk, 'git')
        jk.enable_plugin.assert_called_once_with('git')
        assert result['status'] == 'enabled'


class TestDisablePlugin:
    async def test_disables(self, jk):
        from jenkins_mcp.tools.plugin import disable_plugin
        result = await disable_plugin(jk, 'git')
        jk.disable_plugin.assert_called_once_with('git')
        assert result['status'] == 'disabled'


class TestUninstallPlugin:
    async def test_uninstalls(self, jk):
        from jenkins_mcp.tools.plugin import uninstall_plugin
        result = await uninstall_plugin(jk, 'git')
        jk.uninstall_plugin.assert_called_once_with('git')
        assert result['status'] == 'uninstalled'
