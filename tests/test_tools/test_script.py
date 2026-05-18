import os
import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture
def jk():
    return MagicMock()


class TestRunGroovyScript:
    async def test_runs(self, jk):
        jk.run_script.return_value = 'hello'
        from jenkins_mcp.tools.script import run_groovy_script
        result = await run_groovy_script(jk, 'println "hello"')
        jk.run_script.assert_called_once_with('println "hello"')
        assert result == 'hello'


class TestGetJenkinsInfo:
    async def test_basic(self, jk):
        jk.run_script.return_value = '{}'
        from jenkins_mcp.tools.script import get_jenkins_info
        result = await get_jenkins_info(jk)
        assert isinstance(result, dict)


class TestGetJenkinsVersion:
    async def test_basic(self, jk):
        jk.get_version.return_value = '2.401.1'
        from jenkins_mcp.tools.script import get_jenkins_version
        result = await get_jenkins_version(jk)
        assert result == '2.401.1'


class TestGetWhoami:
    async def test_basic(self, jk):
        jk.get_whoami.return_value = {'id': 'admin'}
        from jenkins_mcp.tools.script import get_whoami
        result = await get_whoami(jk)
        assert result['id'] == 'admin'


class TestVerifyJenkinsCredentials:
    async def test_valid(self):
        from jenkins_mcp.tools.script import verify_jenkins_credentials
        with patch('jenkins_mcp.tools.script.verify_credentials') as mock_vc:
            mock_vc.return_value = {'valid': True, 'username': 'admin'}
            result = await verify_jenkins_credentials('admin', 'token')
            assert result['valid'] is True

    async def test_invalid(self):
        from jenkins_mcp.tools.script import verify_jenkins_credentials
        with patch('jenkins_mcp.tools.script.verify_credentials') as mock_vc:
            mock_vc.return_value = {'valid': False, 'error': 'auth failed'}
            result = await verify_jenkins_credentials('admin', 'bad')
            assert result['valid'] is False


class TestGetSystemMessage:
    async def test_basic(self, jk):
        jk.run_script.return_value = 'System up'
        from jenkins_mcp.tools.script import get_system_message
        result = await get_system_message(jk)
        assert isinstance(result, dict)


class TestGetQuietDownStatus:
    async def test_quiet(self, jk):
        jk.run_script.return_value = 'true'
        from jenkins_mcp.tools.script import get_quiet_down_status
        result = await get_quiet_down_status(jk)
        assert result['quiet_down'] is True

    async def test_active(self, jk):
        jk.run_script.return_value = 'false'
        from jenkins_mcp.tools.script import get_quiet_down_status
        result = await get_quiet_down_status(jk)
        assert result['quiet_down'] is False


class TestAdminActions:
    async def test_set_system_message_no_confirm(self):
        from jenkins_mcp.tools.script import set_system_message
        result = await set_system_message('admin', 'token', 'hello')
        assert 'confirm' in result

    async def test_set_system_message_confirm(self):
        from jenkins_mcp.tools.script import set_system_message
        with patch('jenkins_mcp.tools.script.create_jenkins_client') as mock_cj:
            mock_cj.return_value.run_script.return_value = 'ok'
            result = await set_system_message('admin', 'token', 'hello', confirm=True)
            assert result['status'] == 'set'

    async def test_safe_restart_no_confirm(self):
        from jenkins_mcp.tools.script import safe_restart_jenkins
        result = await safe_restart_jenkins('admin', 'token')
        assert 'confirm' in result

    async def test_safe_restart_confirm(self):
        from jenkins_mcp.tools.script import safe_restart_jenkins
        with patch('jenkins_mcp.tools.script.create_jenkins_client') as mock_cj:
            result = await safe_restart_jenkins('admin', 'token', confirm=True)
            mock_cj.return_value.safe_restart.assert_called_once()

    async def test_quiet_down_no_confirm(self):
        from jenkins_mcp.tools.script import quiet_down_jenkins
        result = await quiet_down_jenkins('admin', 'token')
        assert 'confirm' in result

    async def test_quiet_down_confirm(self):
        from jenkins_mcp.tools.script import quiet_down_jenkins
        with patch('jenkins_mcp.tools.script.create_jenkins_client') as mock_cj:
            result = await quiet_down_jenkins('admin', 'token', confirm=True)
            mock_cj.return_value.quiet_down.assert_called_once()

    async def test_cancel_quiet_down(self):
        from jenkins_mcp.tools.script import cancel_quiet_down_jenkins
        with patch('jenkins_mcp.tools.script.create_jenkins_client') as mock_cj:
            result = await cancel_quiet_down_jenkins('admin', 'token', confirm=True)
            mock_cj.return_value.cancel_quiet_down.assert_called_once()
