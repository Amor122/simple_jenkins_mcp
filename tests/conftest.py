import os
import json
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from requests import Response, Request

os.environ.setdefault('JENKINS_URL', 'http://jenkins:8080')
os.environ.setdefault('JENKINS_USERNAME', 'admin')
os.environ.setdefault('JENKINS_PASSWORD', 'token')


@pytest.fixture
def mock_response():
    def _make(status=200, text='{}', headers=None, json_data=None, reason='OK'):
        resp = MagicMock(spec=Response)
        resp.status_code = status
        resp.text = text if json_data is None else json.dumps(json_data)
        resp.reason = reason
        resp.headers = headers or {}
        if json_data is not None:
            resp.json.return_value = json_data
        else:
            try:
                resp.json.return_value = json.loads(text)
            except Exception:
                resp.json.side_effect = ValueError()
        resp.raise_for_status.return_value = None
        resp.content = resp.text.encode()
        return resp
    return _make


@pytest.fixture
def mock_session(mock_response):
    session = MagicMock()
    session.merge_environment_settings.return_value = {}
    session.prepare_request.side_effect = lambda req: req
    return session


@pytest.fixture
def jenkins(mock_session):
    from jenkins_mcp.jenkins import Jenkins
    jk = Jenkins('http://jenkins:8080', 'admin', 'token')
    jk._session = mock_session
    jk.crumb = False  # disable crumb
    return jk


@pytest.fixture
def mock_jenkins():
    """A fully mocked Jenkins client with common responses pre-configured."""
    from unittest.mock import MagicMock
    jk = MagicMock()
    jk.server = 'http://jenkins:8080/'
    return jk
