"""View管理工具注册"""

from mcp.server.fastmcp import FastMCP

from jenkins_mcp import tools


def register_tools(mcp: FastMCP) -> None:
    """注册View管理工具"""

    def get_jk():
        from jenkins_mcp.server import get_jenkins_client
        return get_jenkins_client()

    @mcp.tool()
    async def get_views():
        """获取所有视图"""
        return await tools.view.get_views(get_jk())

    @mcp.tool()
    async def view_exists(name: str):
        """检查视图是否存在"""
        return await tools.view.view_exists(get_jk(), name)

    @mcp.tool()
    async def get_view_name(name: str):
        """获取视图名称（验证视图存在性）"""
        return await tools.view.get_view_name(get_jk(), name)

    @mcp.tool()
    async def create_view(name: str, config_xml: str):
        """创建视图"""
        return await tools.view.create_view(get_jk(), name, config_xml)

    @mcp.tool()
    async def get_view_config(name: str):
        """获取视图配置XML"""
        return await tools.view.get_view_config(get_jk(), name)

    @mcp.tool()
    async def reconfig_view(name: str, config_xml: str):
        """更新视图配置"""
        return await tools.view.reconfig_view(get_jk(), name, config_xml)

    @mcp.tool()
    async def delete_view(name: str):
        """删除视图"""
        return await tools.view.delete_view(get_jk(), name)
