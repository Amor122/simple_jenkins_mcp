"""Jenkins MCP工具注册"""

from . import lockable_resources
from . import config_file_provider
from . import job_config_history
from . import docker_cloud
from . import kubernetes_cloud
from . import yad_cloud
from . import downstream_buildview
from . import job
from . import build
from . import queue
from . import node
from . import plugin
from . import label
from . import cloud
from . import script

__all__ = ['lockable_resources', 'config_file_provider', 'job_config_history', 'docker_cloud', 'kubernetes_cloud', 'yad_cloud', 'downstream_buildview', 'job', 'build', 'queue', 'node', 'plugin', 'label', 'cloud', 'script']


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
    config_file_provider.register_tools(mcp)
    job_config_history.register_tools(mcp)
    docker_cloud.register_tools(mcp)
    kubernetes_cloud.register_tools(mcp)
    yad_cloud.register_tools(mcp)
    downstream_buildview.register_tools(mcp)