"""Global Properties 管理工具注册"""

from mcp.server.fastmcp import FastMCP

from jenkins_mcp import tools


def register_tools(mcp: FastMCP) -> None:
    """注册Global Properties管理工具"""

    def get_jk():
        from jenkins_mcp.server import get_jenkins_client
        return get_jenkins_client()

    @mcp.tool()
    async def get_global_properties():
        """获取所有Jenkins全局环境变量"""
        return await tools.plugins_management.global_properties.get_global_properties(get_jk())

    @mcp.tool()
    async def set_global_property(username: str, api_token: str, key: str, value: str, confirm: bool = False):
        """设置全局环境变量（新增或更新）

        需要管理员身份。第一次调用时不传 confirm=True 会返回确认信息，
        确认无误后第二次调用时传入 confirm=True 执行。

        参数:
            username: 具有管理员权限的Jenkins用户名
            api_token: Jenkins API Token
            key: 变量名
            value: 变量值
            confirm: 确认执行
        """
        return await tools.plugins_management.global_properties.set_global_property(
            username, api_token, key, value, confirm
        )

    @mcp.tool()
    async def delete_global_property(username: str, api_token: str, key: str, confirm: bool = False):
        """删除全局环境变量

        需要管理员身份。第一次调用时不传 confirm=True 会返回确认信息，
        确认无误后第二次调用时传入 confirm=True 执行。

        参数:
            username: 具有管理员权限的Jenkins用户名
            api_token: Jenkins API Token
            key: 要删除的变量名
            confirm: 确认执行
        """
        return await tools.plugins_management.global_properties.delete_global_property(
            username, api_token, key, confirm
        )
