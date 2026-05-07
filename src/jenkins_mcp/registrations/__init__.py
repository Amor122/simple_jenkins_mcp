"""Jenkins MCP工具注册"""

from . import lockable_resources
from . import job
from . import build
from . import queue
from . import node
from . import plugin
from . import label
from . import cloud
from . import script

__all__ = ['lockable_resources', 'job', 'build', 'queue', 'node', 'plugin', 'label', 'cloud', 'script']


def register_all_tools(mcp) -> None:
    """注册所有工具"""
    job.register_tools(mcp)
    build.register_tools(mcp)
    queue.register_tools(mcp)
    node.register_tools(mcp)
    plugin.register_tools(mcp)
    label.register_tools(mcp)
    cloud.register_tools(mcp)
    script.register_tools(mcp)
    lockable_resources.register_tools(mcp)