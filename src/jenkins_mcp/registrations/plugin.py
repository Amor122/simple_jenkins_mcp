"""Plugin管理工具注册"""

from mcp.server.fastmcp import FastMCP

from jenkins_mcp import tools


def register_tools(mcp: FastMCP) -> None:
    """注册Plugin管理工具"""
    
    def get_jk():
        from jenkins_mcp.server import get_jenkins_client
        return get_jenkins_client()

    @mcp.tool()
    async def get_all_plugins(depth: int = 2):
        """获取所有插件"""
        return await tools.plugin.get_all_plugins(get_jk(), depth)

    @mcp.tool()
    async def get_plugin(short_name: str, depth: int = 2):
        """获取插件详情"""
        return await tools.plugin.get_plugin(get_jk(), short_name, depth)

    @mcp.tool()
    async def get_plugins_with_problems():
        """获取有问题的插件"""
        return await tools.plugin.get_plugins_with_problems(get_jk())