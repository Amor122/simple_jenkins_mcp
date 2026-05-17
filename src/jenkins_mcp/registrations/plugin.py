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

    @mcp.tool()
    async def install_plugin(short_name: str, version: str = None):
        """安装插件

        参数:
            short_name: 插件短名称 (如 "git")
            version: 可选，指定版本（不指定则安装最新版）
        """
        return await tools.plugin.install_plugin(get_jk(), short_name, version)

    @mcp.tool()
    async def enable_plugin(short_name: str):
        """启用插件"""
        return await tools.plugin.enable_plugin(get_jk(), short_name)

    @mcp.tool()
    async def disable_plugin(short_name: str):
        """禁用插件"""
        return await tools.plugin.disable_plugin(get_jk(), short_name)

    @mcp.tool()
    async def uninstall_plugin(short_name: str):
        """卸载插件"""
        return await tools.plugin.uninstall_plugin(get_jk(), short_name)