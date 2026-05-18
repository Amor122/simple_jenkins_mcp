import pytest
from unittest.mock import MagicMock


@pytest.fixture
def jk():
    return MagicMock()


class TestGetAllJobs:
    async def test_basic(self, jk):
        jk.get_all_jobs.return_value = [{'name': 'job1'}, {'name': 'job2'}]
        from jenkins_mcp.tools.job import get_all_jobs
        result = await get_all_jobs(jk)
        assert len(result) == 2
        jk.get_all_jobs.assert_called_once()

    async def test_with_folder_depth(self, jk):
        jk.get_all_jobs.return_value = []
        from jenkins_mcp.tools.job import get_all_jobs
        await get_all_jobs(jk, folder_depth=2)
        jk.get_all_jobs.assert_called_once_with(2)


class TestGetJob:
    async def test_basic(self, jk):
        jk.get_job_info.return_value = {'name': 'test', 'color': 'blue'}
        from jenkins_mcp.tools.job import get_job
        result = await get_job(jk, 'test')
        assert result['name'] == 'test'
        jk.get_job_info.assert_called_once_with('test', 0)

    async def test_with_depth(self, jk):
        from jenkins_mcp.tools.job import get_job
        await get_job(jk, 'folder/job', depth=2)
        jk.get_job_info.assert_called_once_with('folder/job', 2)


class TestGetJobConfig:
    async def test_basic(self, jk):
        jk.get_job_config.return_value = '<xml/>'
        from jenkins_mcp.tools.job import get_job_config
        result = await get_job_config(jk, 'test')
        assert result == '<xml/>'


class TestJobExists:
    async def test_true(self, jk):
        jk.job_exists.return_value = True
        from jenkins_mcp.tools.job import job_exists
        assert await job_exists(jk, 'test') is True

    async def test_false(self, jk):
        jk.job_exists.return_value = False
        from jenkins_mcp.tools.job import job_exists
        assert await job_exists(jk, 'test') is False


class TestCreateJob:
    async def test_creates(self, jk):
        from jenkins_mcp.tools.job import create_job
        result = await create_job(jk, 'new_job', '<xml/>')
        jk.create_job.assert_called_once_with('new_job', '<xml/>')
        assert result['status'] == 'created'
        assert result['name'] == 'new_job'

    async def test_error(self, jk):
        from jenkins_mcp.jenkins import JenkinsException
        jk.create_job.side_effect = JenkinsException('already exists')
        from jenkins_mcp.tools.job import create_job
        result = await create_job(jk, 'dup', '<xml/>')
        assert 'error' in result


class TestSetJobConfig:
    async def test_sets(self, jk):
        from jenkins_mcp.tools.job import set_job_config
        result = await set_job_config(jk, 'test', '<new/>')
        jk.reconfig_job.assert_called_once_with('test', '<new/>')
        assert result['status'] == 'updated'

    async def test_error(self, jk):
        from jenkins_mcp.jenkins import JenkinsException
        jk.reconfig_job.side_effect = JenkinsException('fail')
        from jenkins_mcp.tools.job import set_job_config
        result = await set_job_config(jk, 'test', '<new/>')
        assert 'error' in result


class TestDeleteJob:
    async def test_deletes(self, jk):
        from jenkins_mcp.tools.job import delete_job
        result = await delete_job(jk, 'test')
        jk.delete_job.assert_called_once_with('test')
        assert result['status'] == 'deleted'

    async def test_error(self, jk):
        from jenkins_mcp.jenkins import JenkinsException
        jk.delete_job.side_effect = JenkinsException('fail')
        from jenkins_mcp.tools.job import delete_job
        result = await delete_job(jk, 'test')
        assert 'error' in result


class TestBuildJob:
    async def test_build(self, jk):
        jk.build_job.return_value = 42
        from jenkins_mcp.tools.job import build_job
        result = await build_job(jk, 'test')
        assert result == 42

    async def test_with_params(self, jk):
        jk.build_job.return_value = 43
        from jenkins_mcp.tools.job import build_job
        await build_job(jk, 'test', parameters={'key': 'val'}, token='abc')
        jk.build_job.assert_called_once_with('test', {'key': 'val'}, 'abc')


class TestCopyJob:
    async def test_copies(self, jk):
        from jenkins_mcp.tools.job import copy_job
        result = await copy_job(jk, 'old', 'new')
        jk.copy_job.assert_called_once_with('old', 'new')
        assert result['status'] == 'copied'

    async def test_error(self, jk):
        from jenkins_mcp.jenkins import JenkinsException
        jk.copy_job.side_effect = JenkinsException('fail')
        from jenkins_mcp.tools.job import copy_job
        result = await copy_job(jk, 'old', 'new')
        assert 'error' in result


class TestRenameJob:
    async def test_renames(self, jk):
        from jenkins_mcp.tools.job import rename_job
        result = await rename_job(jk, 'old', 'new')
        jk.rename_job.assert_called_once_with('old', 'new')
        assert result['status'] == 'renamed'

    async def test_error(self, jk):
        from jenkins_mcp.jenkins import JenkinsException
        jk.rename_job.side_effect = JenkinsException('fail')
        from jenkins_mcp.tools.job import rename_job
        result = await rename_job(jk, 'old', 'new')
        assert 'error' in result


class TestEnableDisable:
    async def test_enable(self, jk):
        from jenkins_mcp.tools.job import enable_job
        result = await enable_job(jk, 'test')
        jk.enable_job.assert_called_once_with('test')
        assert result['status'] == 'enabled'

    async def test_disable(self, jk):
        from jenkins_mcp.tools.job import disable_job
        result = await disable_job(jk, 'test')
        jk.disable_job.assert_called_once_with('test')
        assert result['status'] == 'disabled'


class TestSetNextBuildNumber:
    async def test_sets(self, jk):
        from jenkins_mcp.tools.job import set_next_build_number
        result = await set_next_build_number(jk, 'test', 100)
        jk.set_next_build_number.assert_called_once_with('test', 100)
        assert result['status'] == 'set'


class TestWipeoutWorkspace:
    async def test_wipeout(self, jk):
        from jenkins_mcp.tools.job import wipeout_workspace
        result = await wipeout_workspace(jk, 'test')
        jk.wipeout_job_workspace.assert_called_once_with('test')
        assert result['status'] == 'wiped'
