"""Queue管理工具注册"""

from mcp.server.fastmcp import FastMCP

from jenkins_mcp import tools
from jenkins_mcp.registrations.helpers import register_tool


def register_tools(mcp: FastMCP) -> None:
    """注册Queue管理工具"""
    
    def get_jk():
        from jenkins_mcp.server import get_jenkins_client
        return get_jenkins_client()

    @mcp.tool()
    async def get_all_queue_items():
        """获取所有队列项"""
        return await tools.queue.get_all_queue_items(get_jk())

    @mcp.tool()
    async def get_queue_item(id: int, depth: int = 0):
        """获取队列项详情"""
        return await tools.queue.get_queue_item(get_jk(), id, depth)

    @mcp.tool()
    async def get_queue_items_by_job(name: str):
        """获取指定Job的队列项"""
        return await tools.queue.get_queue_items_by_job(get_jk(), name)

    @register_tool(mcp, write_only=True)
    async def cancel_queue_item(id: int):
        """取消队列项"""
        return await tools.queue.cancel_queue_item(get_jk(), id)

    @register_tool(mcp, write_only=True)
    async def cancel_job_queue(name: str):
        """取消Job的队列"""
        return await tools.queue.cancel_job_queue(get_jk(), name)

    @register_tool(mcp, write_only=True)
    async def cancel_all_queue():
        """取消所有队列"""
        return await tools.queue.cancel_all_queue(get_jk())