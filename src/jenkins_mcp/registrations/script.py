"""Script管理工具注册"""

from mcp.server.fastmcp import FastMCP

from jenkins_mcp import tools


def register_tools(mcp: FastMCP) -> None:
    """注册Script管理工具"""
    
    def get_jk():
        from jenkins_mcp.server import get_jenkins_client
        return get_jenkins_client()

    @mcp.tool()
    async def run_groovy_script(script: str, node: str = None):
        """执行任意Groovy脚本"""
        return await tools.script.run_groovy_script(get_jk(), script, node)

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