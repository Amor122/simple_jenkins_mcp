"""Script管理工具注册"""

from mcp.server.fastmcp import FastMCP

from jenkins_mcp import tools


def register_tools(mcp: FastMCP) -> None:
    """注册Script管理工具"""
    
    def get_jk():
        from jenkins_mcp.server import get_jenkins_client
        return get_jenkins_client()

    @mcp.tool()
    async def run_groovy_script(script: str):
        """执行任意Groovy脚本
        
        用于访问Jenkins没有REST API的内部功能
        """
        return await tools.script.run_groovy_script(get_jk(), script)

    @mcp.tool()
    async def get_jenkins_info():
        """获取Jenkins系统信息"""
        return await tools.script.get_jenkins_info(get_jk())

    @mcp.tool()
    async def get_jenkins_version():
        """获取Jenkins版本"""
        return await tools.script.get_jenkins_version(get_jk())

    @mcp.tool()
    async def get_whoami():
        """获取当前认证用户信息"""
        return await tools.script.get_whoami(get_jk())

    @mcp.tool()
    async def verify_jenkins_credentials(username: str, api_token: str):
        """验证Jenkins账户和API Token的有效性及管理员权限

        使用指定的用户名和API Token连接到Jenkins，验证凭据是否有效，
        并检查该用户是否具有管理员权限。
        """
        return await tools.script.verify_jenkins_credentials(username, api_token)

    @mcp.tool()
    async def get_system_message():
        """获取Jenkins系统消息（dashboard上显示的描述信息）"""
        return await tools.script.get_system_message(get_jk())

    @mcp.tool()
    async def set_system_message(username: str, api_token: str, message: str, confirm: bool = False):
        """设置Jenkins系统消息

        需要管理员身份。第一次调用时不传 confirm=True 会返回确认信息，
        确认无误后第二次调用时传入 confirm=True 执行。
        """
        return await tools.script.set_system_message(username, api_token, message, confirm)

    @mcp.tool()
    async def safe_restart_jenkins(username: str, api_token: str, confirm: bool = False):
        """安全重启Jenkins - 等待所有运行中的构建完成后重启

        需要提供具有管理员权限的Jenkins账户和API Token。
        第一次调用时不传 confirm=True 会返回确认信息，
        确认无误后第二次调用时传入 confirm=True 执行。
        """
        return await tools.script.safe_restart_jenkins(username, api_token, confirm)

    @mcp.tool()
    async def restart_jenkins(username: str, api_token: str, confirm: bool = False):
        """强制重启Jenkins - 立即重启（会中断运行中的构建）

        需要提供具有管理员权限的Jenkins账户和API Token。
        第一次调用时不传 confirm=True 会返回确认信息，
        确认无误后第二次调用时传入 confirm=True 执行。
        """
        return await tools.script.restart_jenkins(username, api_token, confirm)

    @mcp.tool()
    async def reload_jenkins_config(username: str, api_token: str, confirm: bool = False):
        """重载Jenkins配置 - 从磁盘重新加载所有配置

        需要提供具有管理员权限的Jenkins账户和API Token。
        第一次调用时不传 confirm=True 会返回确认信息，
        确认无误后第二次调用时传入 confirm=True 执行。
        """
        return await tools.script.reload_jenkins_config(username, api_token, confirm)

    @mcp.tool()
    async def get_quiet_down_status():
        """检查Jenkins是否处于静默模式（quiet down）

        静默模式下 Jenkins 不再接受新的构建请求。
        """
        return await tools.script.get_quiet_down_status(get_jk())

    @mcp.tool()
    async def quiet_down_jenkins(username: str, api_token: str, confirm: bool = False):
        """设置Jenkins静默模式 - 不再接受新构建

        需要管理员身份。第一次调用时不传 confirm=True 会返回确认信息，
        确认无误后第二次调用时传入 confirm=True 执行。
        """
        return await tools.script.quiet_down_jenkins(username, api_token, confirm)

    @mcp.tool()
    async def cancel_quiet_down_jenkins(username: str, api_token: str, confirm: bool = False):
        """取消Jenkins静默模式 - 恢复正常接受构建

        需要管理员身份。第一次调用时不传 confirm=True 会返回确认信息，
        确认无误后第二次调用时传入 confirm=True 执行。
        """
        return await tools.script.cancel_quiet_down_jenkins(username, api_token, confirm)