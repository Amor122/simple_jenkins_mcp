"""Jenkins 资源注册 - 通过 URI 暴露只读数据

资源 URI 模板:
  jenkins://jobs                         所有 Job 列表
  jenkins://job/{name}/config            Job 配置 XML
  jenkins://job/{name}/build/{number}    Build 信息
  jenkins://job/{name}/build/{number}/console  构建日志
  jenkins://system/version               Jenkins 版本
  jenkins://system/info                  Jenkins 系统信息
  jenkins://queue                        队列项
"""

from mcp.server.fastmcp import FastMCP


def register_resources(mcp: FastMCP) -> None:
    """注册资源"""

    def get_jk():
        from jenkins_mcp.server import get_jenkins_client
        return get_jenkins_client()

    @mcp.resource("jenkins://jobs")
    async def get_all_jobs() -> list:
        """所有 Job 列表"""
        return get_jk().get_all_jobs()

    @mcp.resource("jenkins://job/{name}/config")
    async def get_job_config(name: str) -> str:
        """Job 配置 XML"""
        return get_jk().get_job_config(name)

    @mcp.resource("jenkins://job/{name}/build/{number}")
    async def get_build_info(name: str, number: int) -> dict:
        """Build 信息"""
        return get_jk().get_build_info(name, number)

    @mcp.resource("jenkins://job/{name}/build/{number}/console")
    async def get_build_console(name: str, number: int) -> str:
        """构建日志"""
        return get_jk().get_build_console_output(name, number)

    @mcp.resource("jenkins://system/version")
    async def get_version() -> str:
        """Jenkins 版本"""
        return get_jk().get_version()

    @mcp.resource("jenkins://system/info")
    async def get_system_info() -> dict:
        """Jenkins 系统信息"""
        return get_jk().get_info()

    @mcp.resource("jenkins://queue")
    async def get_queue() -> list:
        """队列项"""
        return get_jk().get_queue_info()
