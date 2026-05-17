"""注册辅助工具 - 条件性工具注册装饰器

当 JENKINS_READ_ONLY=true 时，write_only 级别的工具直接不注册到 MCP，
而不是注册后运行时才拒绝。
"""

import os
from functools import wraps


def register_tool(mcp, write_only=False):
    """条件性工具注册装饰器

    当 JENKINS_READ_ONLY=true 且 write_only=True 时，
    跳过注册该工具，使其对客户端完全不可见。

    用法:
        @register_tool(mcp)
        async def read_tool(): ...

        @register_tool(mcp, write_only=True)
        async def write_tool(): ...
    """
    read_only = os.environ.get('JENKINS_READ_ONLY', 'false').lower() == 'true'

    if read_only and write_only:
        def noop(func):
            return func
        return noop

    return mcp.tool()
