import os
import pytest
from unittest.mock import MagicMock, patch


class TestCheckReadOnly:
    def test_not_read_only(self):
        os.environ.pop('JENKINS_READ_ONLY', None)
        from jenkins_mcp.tools.utils import check_read_only
        check_read_only({'tag1'})  # should not raise

    def test_read_only_with_write_tag(self):
        os.environ['JENKINS_READ_ONLY'] = 'true'
        from jenkins_mcp.tools.utils import check_read_only
        from jenkins_mcp.jenkins import JenkinsException
        with pytest.raises(JenkinsException, match='只读模式'):
            check_read_only({'write'})
        del os.environ['JENKINS_READ_ONLY']

    def test_read_only_with_read_tag(self):
        os.environ['JENKINS_READ_ONLY'] = 'true'
        from jenkins_mcp.tools.utils import check_read_only
        check_read_only({'read'})  # should not raise
        del os.environ['JENKINS_READ_ONLY']


class TestAdminOnly:
    def test_wraps_and_calls(self):
        from jenkins_mcp.tools.utils import admin_only
        func = MagicMock(return_value='ok')
        wrapped = admin_only(func)
        result = wrapped(MagicMock(), 'arg1')
        assert result == 'ok'

    def test_wraps_read_only_blocked(self):
        os.environ['JENKINS_READ_ONLY'] = 'true'
        from jenkins_mcp.tools.utils import admin_only
        from jenkins_mcp.jenkins import JenkinsException
        func = MagicMock()
        wrapped = admin_only(func)
        with pytest.raises(JenkinsException, match='只读模式'):
            wrapped(MagicMock())
        func.assert_not_called()
        del os.environ['JENKINS_READ_ONLY']


class TestWriteOnly:
    def test_wraps_and_calls(self):
        from jenkins_mcp.tools.utils import write_only
        func = MagicMock(return_value='ok')
        wrapped = write_only(func)
        result = wrapped(MagicMock(), 'arg1')
        assert result == 'ok'

    def test_wraps_read_only_blocked(self):
        os.environ['JENKINS_READ_ONLY'] = 'true'
        from jenkins_mcp.tools.utils import write_only
        from jenkins_mcp.jenkins import JenkinsException
        func = MagicMock()
        wrapped = write_only(func)
        with pytest.raises(JenkinsException, match='只读模式'):
            wrapped(MagicMock())
        func.assert_not_called()
        del os.environ['JENKINS_READ_ONLY']


class TestCreateJenkinsClient:
    def test_creates_client(self):
        from jenkins_mcp.tools.utils import create_jenkins_client
        with patch('jenkins_mcp.tools.utils.Jenkins') as MockJenkins:
            client = create_jenkins_client('user', 'token')
            MockJenkins.assert_called_once()
            assert client == MockJenkins.return_value

    def test_passes_credentials(self):
        from jenkins_mcp.tools.utils import create_jenkins_client
        with patch('jenkins_mcp.tools.utils.Jenkins') as MockJenkins:
            create_jenkins_client('myuser', 'mytoken')
            _, kwargs = MockJenkins.call_args
            assert kwargs['username'] == 'myuser'
            assert kwargs['password'] == 'mytoken'


class TestVerifyCredentials:
    def test_success(self):
        from jenkins_mcp.tools.utils import verify_credentials
        mock_client = MagicMock()
        mock_client.get_whoami.return_value = {'id': 'admin'}
        mock_client.get_version.return_value = '2.401'

        with patch('jenkins_mcp.tools.utils.create_jenkins_client', return_value=mock_client):
            result = verify_credentials('user', 'token')
            assert result['valid'] is True
            assert result['username'] == 'admin'
            assert result['version'] == '2.401'

    def test_failure(self):
        from jenkins_mcp.tools.utils import verify_credentials
        from jenkins_mcp.jenkins import JenkinsException

        with patch('jenkins_mcp.tools.utils.create_jenkins_client') as mock_create:
            mock_client = MagicMock()
            mock_client.get_whoami.side_effect = JenkinsException('auth failed')
            mock_create.return_value = mock_client

            result = verify_credentials('user', 'bad_token')
            assert result['valid'] is False
            assert 'auth failed' in result['error']
