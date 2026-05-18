import pytest
from unittest.mock import MagicMock


@pytest.fixture
def jk():
    return MagicMock()


class TestGetBuild:
    async def test_basic(self, jk):
        jk.get_build_info.return_value = {'number': 42, 'result': 'SUCCESS'}
        from jenkins_mcp.tools.build import get_build
        result = await get_build(jk, 'test', 42)
        assert result['number'] == 42
        jk.get_build_info.assert_called_once_with('test', 42, 0)

    async def test_with_depth(self, jk):
        from jenkins_mcp.tools.build import get_build
        await get_build(jk, 'test', 42, depth=2)
        jk.get_build_info.assert_called_once_with('test', 42, 2)


class TestGetBuildConsoleOutput:
    async def test_full(self, jk):
        jk.get_build_console_output.return_value = 'line1\nline2\n'
        from jenkins_mcp.tools.build import get_build_console_output
        result = await get_build_console_output(jk, 'test', 42)
        assert 'line1' in result
        jk.get_build_console_output.assert_called_once_with('test', 42)

    async def test_with_offset_limit(self, jk):
        jk.get_build_console_output.return_value = 'a\nb\nc\nd\ne\n'
        from jenkins_mcp.tools.build import get_build_console_output
        result = await get_build_console_output(jk, 'test', 42, offset=2, limit=2)
        lines = result.strip().split('\n')
        assert lines == ['c', 'd']


class TestGetRunningBuilds:
    async def test_basic(self, jk):
        jk.get_running_builds.return_value = [{'name': 'job1', 'number': 5}]
        from jenkins_mcp.tools.build import get_running_builds
        result = await get_running_builds(jk)
        assert len(result) == 1


class TestStopBuild:
    async def test_stops(self, jk):
        from jenkins_mcp.tools.build import stop_build
        result = await stop_build(jk, 'test', 42)
        jk.stop_build.assert_called_once_with('test', 42)
        assert result['status'] == 'stopped'


class TestDeleteBuild:
    async def test_deletes(self, jk):
        from jenkins_mcp.tools.build import delete_build
        result = await delete_build(jk, 'test', 42)
        jk.delete_build.assert_called_once_with('test', 42)
        assert result['status'] == 'deleted'


class TestStopAllBuilds:
    async def test_stops_all(self, jk):
        jk.get_running_builds.return_value = [
            {'name': 'job1', 'number': 1},
            {'name': 'job1', 'number': 2},
        ]
        from jenkins_mcp.tools.build import stop_all_builds
        result = await stop_all_builds(jk)
        assert jk.stop_build.call_count == 2
        assert result['stopped'] == 2

    async def test_stops_for_job(self, jk):
        jk.get_running_builds.return_value = [
            {'name': 'job1', 'number': 1},
            {'name': 'job2', 'number': 2},
        ]
        from jenkins_mcp.tools.build import stop_all_builds
        result = await stop_all_builds(jk, name='job1')
        jk.stop_build.assert_called_once_with('job1', 1)
        assert result['stopped'] == 1

    async def test_none_running(self, jk):
        jk.get_running_builds.return_value = []
        from jenkins_mcp.tools.build import stop_all_builds
        result = await stop_all_builds(jk)
        assert result['stopped'] == 0


class TestGetBuildArtifacts:
    async def test_basic(self, jk):
        jk.get_build_artifacts.return_value = [{'relativePath': 'data.txt'}]
        from jenkins_mcp.tools.build import get_build_artifacts
        result = await get_build_artifacts(jk, 'test', 42)
        assert len(result) == 1
        jk.get_build_artifacts.assert_called_once_with('test', 42)


class TestGetBuildArtifact:
    async def test_basic(self, jk):
        jk.get_build_artifact.return_value = {'content': 'data'}
        from jenkins_mcp.tools.build import get_build_artifact
        result = await get_build_artifact(jk, 'test', 42, 'data.txt')
        jk.get_build_artifact.assert_called_once_with('test', 42, 'data.txt')


class TestDownloadBuildArtifact:
    async def test_download(self, jk):
        from jenkins_mcp.tools.build import download_build_artifact
        result = await download_build_artifact(jk, 'test', 42, 'data.txt', '/tmp/out')
        jk.get_build_artifact_to_file.assert_called_once_with('test', 42, 'data.txt', '/tmp/out')
        assert result['status'] == 'downloaded'


class TestDownloadAllArtifacts:
    async def test_download_all(self, jk):
        jk.get_build_artifacts.return_value = [
            {'relativePath': 'a.txt'},
            {'relativePath': 'b.txt'},
        ]
        jk.get_build_artifact_to_file.return_value = {'file': '/tmp/out/x', 'size': 10}
        from jenkins_mcp.tools.build import download_all_artifacts
        result = await download_all_artifacts(jk, 'test', 42, '/tmp/out')
        assert len(result) == 2

    async def test_no_artifacts(self, jk):
        jk.get_build_artifacts.return_value = []
        from jenkins_mcp.tools.build import download_all_artifacts
        result = await download_all_artifacts(jk, 'test', 42, '/tmp/out')
        assert result == []


class TestGetBuildEnvVars:
    async def test_basic(self, jk):
        jk.get_build_env_vars.return_value = {'VAR': 'val'}
        from jenkins_mcp.tools.build import get_build_env_vars
        result = await get_build_env_vars(jk, 'test', 42)
        jk.get_build_env_vars.assert_called_once_with('test', 42)
        assert result == {'VAR': 'val'}


class TestDiffBuildEnvVars:
    async def test_diff(self, jk):
        jk.get_build_env_vars.side_effect = [
            {'A': '1', 'B': '2', 'C': '3'},
            {'A': '1', 'B': '20', 'D': '4'},
        ]
        from jenkins_mcp.tools.build import diff_build_env_vars
        result = await diff_build_env_vars(jk, 'test', 1, 2)
        assert set(result['added']) == {'D'}
        assert set(result['removed']) == {'C'}
        assert set(result['changed']) == {'B'}
        assert result['summary'] == {'build1': 3, 'build2': 3, 'added': 1, 'removed': 1, 'changed': 1}

    async def test_same(self, jk):
        jk.get_build_env_vars.side_effect = [
            {'A': '1', 'B': '2'},
            {'A': '1', 'B': '2'},
        ]
        from jenkins_mcp.tools.build import diff_build_env_vars
        result = await diff_build_env_vars(jk, 'test', 1, 2)
        assert result['added'] == []
        assert result['removed'] == []
        assert result['changed'] == []
