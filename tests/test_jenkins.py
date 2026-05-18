import json
import pytest
import requests
from unittest.mock import MagicMock, call
from jenkins_mcp.jenkins import (
    Jenkins, JenkinsException, NotFoundException,
    TimeoutException, BadHTTPException
)


class TestInit:
    def test_basic_init(self):
        j = Jenkins('http://jenkins:8080', 'u', 'p')
        assert j.server == 'http://jenkins:8080/'
        assert j.timeout == 30
        assert j._session.auth is not None

    def test_no_auth(self):
        j = Jenkins('http://jenkins:8080')
        assert j._session.auth is None

    def test_verify_ssl_false(self):
        j = Jenkins('http://jenkins:8080', verify_ssl=False)
        assert j._session.verify is False


class TestGetJobFolder:
    def test_simple_name(self, jenkins):
        folder, short = jenkins._get_job_folder('myjob')
        assert folder == ''
        assert short == 'myjob'

    def test_folder_path(self, jenkins):
        folder, short = jenkins._get_job_folder('folder/sub/myjob')
        assert folder == 'job/folder/job/sub/'
        assert short == 'myjob'

    def test_deep_folder(self, jenkins):
        folder, short = jenkins._get_job_folder('a/b/c/d')
        assert folder == 'job/a/job/b/job/c/'
        assert short == 'd'


class TestBuildUrl:
    def test_no_vars(self, jenkins):
        url = jenkins._build_url('api/json')
        assert url == 'http://jenkins:8080/api/json'

    def test_with_vars(self, jenkins):
        params = {'folder_url': 'job/folder/', 'short_name': 'test', 'depth': 0}
        url = jenkins._build_url(
            '%(folder_url)sjob/%(short_name)s/api/json?depth=%(depth)s',
            params
        )
        assert 'job/folder/' in url
        assert '/job/test/' in url

    def test_encoded_vars(self, jenkins):
        params = {'short_name': 'my job', 'folder_url': ''}
        url = jenkins._build_url('%(folder_url)sjob/%(short_name)s/config.xml', params)
        assert 'my+job' in url or 'my%20job' in url


class TestJenkinsRequest:
    def test_success(self, jenkins, mock_response):
        resp = mock_response(200, 'ok')
        jenkins._session.send.return_value = resp
        result = jenkins.jenkins_request(requests.Request('GET', 'http://jenkins:8080/'))
        assert result.text == 'ok'

    def test_403_retry(self, jenkins, mock_response):
        jenkins.crumb = {'crumbRequestField': 'crumb', 'crumb': 'abc'}
        first = MagicMock()
        first.status_code = 403
        first.raise_for_status.side_effect = requests.exceptions.HTTPError(response=first)
        first.reason = 'Forbidden'
        first.text = ''
        second = mock_response(200, 'ok')

        jenkins._session.send.side_effect = [first, second]
        result = jenkins.jenkins_request(requests.Request('GET', 'http://jenkins:8080/'))
        assert result.text == 'ok'
        assert jenkins.crumb is None  # was reset

    def test_404_raises_notfound(self, jenkins):
        resp = MagicMock()
        resp.status_code = 404
        resp.raise_for_status.side_effect = requests.exceptions.HTTPError(response=resp)
        resp.reason = 'Not Found'
        resp.text = ''
        jenkins._session.send.return_value = resp
        with pytest.raises(NotFoundException):
            jenkins.jenkins_request(requests.Request('GET', 'http://jenkins:8080/'))

    def test_timeout_raises_timeout(self, jenkins):
        jenkins._session.send.side_effect = requests.exceptions.Timeout('timeout')
        with pytest.raises(TimeoutException):
            jenkins.jenkins_request(requests.Request('GET', 'http://jenkins:8080/'))

    def test_auth_failure(self, jenkins):
        resp = MagicMock()
        resp.status_code = 401
        resp.raise_for_status.side_effect = requests.exceptions.HTTPError(response=resp)
        resp.reason = 'Unauthorized'
        resp.text = 'Auth failed'
        jenkins._session.send.return_value = resp
        with pytest.raises(JenkinsException, match='authentication failed'):
            jenkins.jenkins_request(requests.Request('GET', 'http://jenkins:8080/'))


class TestCrumb:
    def test_crumb_success(self, jenkins, mock_response):
        jenkins._session.send.return_value = mock_response(
            200, json_data={'crumb': 'xyz', 'crumbRequestField': 'Jenkins-Crumb'}
        )
        jenkins.maybe_add_crumb(requests.Request('GET', 'http://jenkins:8080/'))
        assert jenkins.crumb == {'crumb': 'xyz', 'crumbRequestField': 'Jenkins-Crumb'}

    def test_crumb_disabled(self, jenkins):
        jenkins.crumb = False
        req = requests.Request('GET', 'http://jenkins:8080/')
        jenkins.maybe_add_crumb(req)
        assert 'Jenkins-Crumb' not in (req.headers or {})

    def test_crumb_not_found(self, jenkins, mock_response):
        resp = mock_response(200, '')
        resp.json.side_effect = ValueError()
        jenkins._session.send.return_value = resp
        jenkins.maybe_add_crumb(requests.Request('GET', 'http://jenkins:8080/'))
        assert jenkins.crumb is False


class TestJobMethods:
    def test_get_job_info(self, jenkins, mock_response):
        jenkins._session.send.return_value = mock_response(
            200, json_data={'name': 'test', 'color': 'blue'}
        )
        info = jenkins.get_job_info('test')
        assert info['name'] == 'test'

    def test_get_job_info_folder(self, jenkins, mock_response):
        jenkins._session.send.return_value = mock_response(
            200, json_data={'name': 'myjob', 'fullName': 'folder/myjob'}
        )
        info = jenkins.get_job_info('folder/myjob')
        assert info['name'] == 'myjob'

    def test_get_job_config(self, jenkins, mock_response):
        xml = '<project><name>test</name></project>'
        jenkins._session.send.return_value = mock_response(200, xml)
        config = jenkins.get_job_config('test')
        assert '<name>test</name>' in config

    def test_job_exists_true(self, jenkins, mock_response):
        jenkins._session.send.return_value = mock_response(
            200, json_data={'name': 'test'}
        )
        assert jenkins.job_exists('test') is True

    def test_job_exists_false(self, jenkins):
        from jenkins_mcp.jenkins import NotFoundException
        resp = MagicMock()
        resp.status_code = 404
        resp.raise_for_status.side_effect = requests.exceptions.HTTPError(response=resp)
        resp.reason = 'Not Found'
        resp.text = ''
        jenkins._session.send.return_value = resp
        assert jenkins.job_exists('nonexistent') is False

    def test_create_job(self, jenkins, mock_response):
        jenkins._session.send.return_value = mock_response(200, '')
        from unittest.mock import PropertyAttribute

        with pytest.raises(JenkinsException, match='already exists'):
            j = jenkins
            j._get_job_folder = lambda n: ('', n)
            orig_exists = j.job_exists
            j.job_exists = lambda n: True
            try:
                j.create_job('test', '<xml/>')
            finally:
                j.job_exists = orig_exists

    def test_delete_job(self, jenkins, mock_response):
        jenkins._session.send.return_value = mock_response(200, '')
        jenkins.delete_job('test')

    def test_enable_job(self, jenkins, mock_response):
        jenkins._session.send.return_value = mock_response(200, '')
        jenkins.enable_job('test')

    def test_disable_job(self, jenkins, mock_response):
        jenkins._session.send.return_value = mock_response(200, '')
        jenkins.disable_job('test')

    def test_get_all_jobs(self, jenkins, mock_response):
        jenkins._session.send.return_value = mock_response(
            200, json_data={'jobs': [{'name': 'job1'}, {'name': 'job2'}]}
        )
        jobs = jenkins.get_all_jobs()
        assert len(jobs) == 2

    def test_build_job(self, jenkins, mock_response):
        resp = mock_response(201, '', headers={'Location': 'http://jenkins:8080/queue/item/42'})
        resp.status_code = 201
        jenkins._session.send.return_value = resp
        qid = jenkins.build_job('test')
        assert qid == 42

    def test_copy_job_same_folder(self, jenkins, mock_response):
        jenkins._session.send.return_value = mock_response(200, '')
        jenkins.job_exists = lambda n: n == 'new_job'
        jenkins.copy_job('old_job', 'new_job')

    def test_copy_job_diff_folder(self, jenkins):
        with pytest.raises(JenkinsException, match='folder must be the same'):
            jenkins.copy_job('folder/old', 'other/new')


class TestBuildMethods:
    def test_get_build_info(self, jenkins, mock_response):
        jenkins._session.send.return_value = mock_response(
            200, json_data={'number': 42, 'result': 'SUCCESS'}
        )
        info = jenkins.get_build_info('test', 42)
        assert info['number'] == 42

    def test_get_build_console_output(self, jenkins, mock_response):
        jenkins._session.send.return_value = mock_response(200, 'line1\nline2\n')
        output = jenkins.get_build_console_output('test', 42)
        assert output == 'line1\nline2\n'

    def test_stop_build(self, jenkins, mock_response):
        jenkins._session.send.return_value = mock_response(200, '')
        jenkins.stop_build('test', 42)

    def test_delete_build(self, jenkins, mock_response):
        jenkins._session.send.return_value = mock_response(200, '')
        jenkins.delete_build('test', 42)

    def test_get_build_env_vars_injected(self, jenkins, mock_response):
        jenkins._session.send.return_value = mock_response(
            200, json_data={'envMap': {'VAR1': 'val1', 'VAR2': 'val2'}}
        )
        env = jenkins.get_build_env_vars('test', 42)
        assert env == {'VAR1': 'val1', 'VAR2': 'val2'}

    def test_get_build_env_vars_fallback(self, jenkins, mock_response):
        first_resp = MagicMock()
        first_resp.status_code = 500
        first_resp.raise_for_status.side_effect = requests.exceptions.HTTPError(response=first_resp)
        first_resp.reason = 'Error'
        first_resp.text = ''
        second_resp = mock_response(
            200, json_data={
                'actions': [
                    {'_class': 'ParametersAction', 'parameters': [{'name': 'PARAM1', 'value': 'v1'}]},
                    {'_class': 'EnvironmentContributingAction', 'env': {'VAR2': 'v2'}},
                ]
            }
        )
        jenkins._session.send.side_effect = [first_resp, second_resp]
        env = jenkins.get_build_env_vars('test', 42)
        assert env.get('PARAM1') == 'v1'
        assert env.get('VAR2') == 'v2'

    def test_get_build_artifact_text(self, jenkins, mock_response):
        jenkins._session.send.return_value = mock_response(200, 'artifact content')
        result = jenkins.get_build_artifact('test', 42, 'data.txt')
        assert result['content'] == 'artifact content'

    def test_get_build_artifacts(self, jenkins, mock_response):
        jenkins._session.send.return_value = mock_response(
            200, json_data={'artifacts': [{'relativePath': 'data.txt', 'fileName': 'data.txt'}]}
        )
        artifacts = jenkins.get_build_artifacts('test', 42)
        assert len(artifacts) == 1


class TestQueueMethods:
    def test_get_queue_info(self, jenkins, mock_response):
        jenkins._session.send.return_value = mock_response(
            200, json_data={'items': [{'id': 1}, {'id': 2}]}
        )
        items = jenkins.get_queue_info()
        assert len(items) == 2

    def test_get_queue_item(self, jenkins, mock_response):
        jenkins._session.send.return_value = mock_response(
            200, json_data={'id': 1, 'task': {'name': 'test'}}
        )
        item = jenkins.get_queue_item(1)
        assert item['id'] == 1

    def test_cancel_queue(self, jenkins, mock_response):
        jenkins._session.send.return_value = mock_response(200, '')
        jenkins.cancel_queue(1)


class TestNodeMethods:
    def test_get_nodes(self, jenkins, mock_response):
        jenkins._session.send.return_value = mock_response(
            200, json_data={'computer': [{'displayName': 'master'}]}
        )
        nodes = jenkins.get_nodes()
        assert len(nodes) == 1

    def test_get_node_info(self, jenkins, mock_response):
        jenkins._session.send.return_value = mock_response(
            200, json_data={'displayName': 'agent1', 'offline': False}
        )
        info = jenkins.get_node_info('agent1')
        assert info['displayName'] == 'agent1'

    def test_node_exists_true(self, jenkins, mock_response):
        jenkins._session.send.return_value = mock_response(
            200, json_data={'displayName': 'agent1'}
        )
        assert jenkins.node_exists('agent1') is True

    def test_node_exists_false(self, jenkins):
        from jenkins_mcp.jenkins import NotFoundException
        resp = MagicMock()
        resp.status_code = 404
        resp.raise_for_status.side_effect = requests.exceptions.HTTPError(response=resp)
        resp.reason = 'Not Found'
        resp.text = ''
        jenkins._session.send.return_value = resp
        assert jenkins.node_exists('nonexistent') is False

    def test_delete_node_builtin(self, jenkins):
        with pytest.raises(JenkinsException, match='cannot delete built-in node'):
            jenkins.delete_node('master')

    def test_create_node(self, jenkins, mock_response):
        jenkins._session.send.return_value = mock_response(200, '')
        jenkins.node_exists = lambda n: n != 'new_node'

        before_exists = jenkins.node_exists
        def exists_side_effect(name):
            if name == 'new_node':
                return False
            return before_exists(name)
        jenkins.node_exists = exists_side_effect


class TestPluginMethods:
    def test_get_plugins(self, jenkins, mock_response):
        jenkins._session.send.return_value = mock_response(
            200, json_data={'plugins': [{'shortName': 'git'}]}
        )
        plugins = jenkins.get_plugins()
        assert len(plugins) == 1

    def test_get_plugin_info(self, jenkins, mock_response):
        jenkins._session.send.return_value = mock_response(
            200, json_data={'plugins': [{'shortName': 'git', 'version': '1.0'}]}
        )
        plugin = jenkins.get_plugin_info('git')
        assert plugin['shortName'] == 'git'

    def test_install_plugin(self, jenkins, mock_response):
        jenkins._session.send.return_value = mock_response(200, '')
        result = jenkins.install_plugin('git')
        assert result['status'] == 'installed'

    def test_uninstall_plugin(self, jenkins, mock_response):
        jenkins._session.send.return_value = mock_response(200, '')
        jenkins.uninstall_plugin('git')

    def test_enable_plugin(self, jenkins, mock_response):
        jenkins._session.send.return_value = mock_response(200, '')
        jenkins.enable_plugin('git')

    def test_disable_plugin(self, jenkins, mock_response):
        jenkins._session.send.return_value = mock_response(200, '')
        jenkins.disable_plugin('git')


class TestViewMethods:
    def test_get_views(self, jenkins, mock_response):
        jenkins._session.send.return_value = mock_response(
            200, json_data={'views': [{'name': 'All'}, {'name': 'MyView'}]}
        )
        views = jenkins.get_views()
        assert len(views) == 2

    def test_view_exists_true(self, jenkins, mock_response):
        jenkins._session.send.return_value = mock_response(
            200, json_data={'name': 'All'}
        )
        assert jenkins.view_exists('All') is True

    def test_view_exists_false(self, jenkins):
        resp = MagicMock()
        resp.status_code = 404
        resp.raise_for_status.side_effect = requests.exceptions.HTTPError(response=resp)
        jenkins._session.send.return_value = resp
        assert jenkins.view_exists('NoView') is False

    def test_create_view(self, jenkins, mock_response):
        jenkins._session.send.return_value = mock_response(200, '')
        def ve(name):
            return False
        orig_ve = jenkins.view_exists
        jenkins.view_exists = ve
        try:
            jenkins.create_view('NewView', '<xml/>')
        finally:
            jenkins.view_exists = orig_ve


class TestScriptMethods:
    def test_run_script(self, jenkins, mock_response):
        jenkins._session.send.return_value = mock_response(200, 'Result: hello')
        result = jenkins.run_script('println "hello"')
        assert result == 'hello'

    def test_run_script_no_prefix(self, jenkins, mock_response):
        jenkins._session.send.return_value = mock_response(200, 'some output')
        with pytest.raises(JenkinsException):
            jenkins.run_script('bad script')


class TestSystemMethods:
    def test_get_info(self, jenkins, mock_response):
        jenkins._session.send.return_value = mock_response(
            200, json_data={'nodeDescription': 'Jenkins master'}
        )
        info = jenkins.get_info()
        assert info['nodeDescription'] == 'Jenkins master'

    def test_get_version(self, jenkins, mock_response):
        resp = mock_response(200, '', headers={'X-Jenkins': '2.401.1'})
        jenkins._session.send.return_value = resp
        version = jenkins.get_version()
        assert version == '2.401.1'

    def test_get_whoami(self, jenkins, mock_response):
        jenkins._session.send.return_value = mock_response(
            200, json_data={'id': 'admin'}
        )
        who = jenkins.get_whoami()
        assert who['id'] == 'admin'

    def test_quiet_down(self, jenkins, mock_response):
        jenkins._session.send.return_value = mock_response(200, '')
        jenkins.quiet_down()

    def test_safe_restart(self, jenkins, mock_response):
        jenkins._session.send.return_value = mock_response(200, '')
        jenkins.safe_restart()
