import os
import pytest
from unittest.mock import MagicMock


class TestRegisterTool:
    def test_normal_mode(self):
        os.environ.pop('JENKINS_READ_ONLY', None)
        from jenkins_mcp.registrations.helpers import register_tool
        mcp = MagicMock()
        decorator = register_tool(mcp, write_only=False)
        func = MagicMock()
        result = decorator(func)
        mcp.tool.return_value.assert_called_once_with(func)

    def test_read_only_blocks_write_only(self):
        os.environ['JENKINS_READ_ONLY'] = 'true'
        from jenkins_mcp.registrations.helpers import register_tool
        mcp = MagicMock()
        decorator = register_tool(mcp, write_only=True)
        func = MagicMock()
        result = decorator(func)
        mcp.tool.assert_not_called()
        assert result == func  # noop, returns original func
        del os.environ['JENKINS_READ_ONLY']

    def test_read_only_allows_read_tools(self):
        os.environ['JENKINS_READ_ONLY'] = 'true'
        from jenkins_mcp.registrations.helpers import register_tool
        mcp = MagicMock()
        decorator = register_tool(mcp, write_only=False)
        func = MagicMock()
        result = decorator(func)
        mcp.tool.return_value.assert_called_once_with(func)
        del os.environ['JENKINS_READ_ONLY']

    def test_false_string(self):
        os.environ['JENKINS_READ_ONLY'] = 'false'
        from jenkins_mcp.registrations.helpers import register_tool
        mcp = MagicMock()
        decorator = register_tool(mcp, write_only=True)
        func = MagicMock()
        result = decorator(func)
        mcp.tool.return_value.assert_called_once_with(func)
        del os.environ['JENKINS_READ_ONLY']
