"""Job管理工具注册"""

from mcp.server.fastmcp import FastMCP

from jenkins_mcp import tools
from jenkins_mcp.registrations.helpers import register_tool


def register_tools(mcp: FastMCP) -> None:
    """注册Job管理工具"""
    
    def get_jk():
        from jenkins_mcp.server import get_jenkins_client
        return get_jenkins_client()

    @mcp.tool()
    async def get_all_jobs(folder_depth: int = None):
        """获取所有Job列表"""
        return await tools.job.get_all_jobs(get_jk(), folder_depth)

    @mcp.tool()
    async def get_job(name: str, depth: int = 0):
        """获取指定Job信息"""
        return await tools.job.get_job(get_jk(), name, depth)

    @mcp.tool()
    async def get_job_config(name: str):
        """获取Job配置XML"""
        return await tools.job.get_job_config(get_jk(), name)

    @register_tool(mcp, write_only=True)
    async def set_job_config(name: str, config_xml: str):
        """设置Job配置"""
        return await tools.job.set_job_config(get_jk(), name, config_xml)

    @register_tool(mcp, write_only=True)
    async def create_job(name: str, config_xml: str):
        """创建新Job"""
        return await tools.job.create_job(get_jk(), name, config_xml)

    @register_tool(mcp, write_only=True)
    async def delete_job(name: str):
        """删除Job"""
        return await tools.job.delete_job(get_jk(), name)

    @register_tool(mcp, write_only=True)
    async def copy_job(from_name: str, to_name: str):
        """复制Job"""
        return await tools.job.copy_job(get_jk(), from_name, to_name)

    @register_tool(mcp, write_only=True)
    async def enable_job(name: str):
        """启用Job"""
        return await tools.job.enable_job(get_jk(), name)

    @register_tool(mcp, write_only=True)
    async def disable_job(name: str):
        """禁用Job"""
        return await tools.job.disable_job(get_jk(), name)

    @register_tool(mcp, write_only=True)
    async def build_job(name: str, parameters: dict = None, token: str = None):
        """触发构建"""
        return await tools.job.build_job(get_jk(), name, parameters, token)

    @register_tool(mcp, write_only=True)
    async def rename_job(name: str, new_name: str):
        """重命名Job"""
        return await tools.job.rename_job(get_jk(), name, new_name)

    @register_tool(mcp, write_only=True)
    async def set_next_build_number(name: str, number: int):
        """设置下一个构建号"""
        return await tools.job.set_next_build_number(get_jk(), name, number)

    @register_tool(mcp, write_only=True)
    async def wipeout_workspace(name: str):
        """清空工作区"""
        return await tools.job.wipeout_workspace(get_jk(), name)

    @mcp.tool()
    async def job_exists(name: str):
        """检查Job是否存在"""
        return await tools.job.job_exists(get_jk(), name)
