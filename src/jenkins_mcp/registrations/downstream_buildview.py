"""Downstream Build View Plugin管理工具注册"""

from mcp.server.fastmcp import FastMCP

from jenkins_mcp import tools


def register_tools(mcp: FastMCP) -> None:
    """注册Downstream Build View Plugin管理工具"""

    def get_jk():
        from jenkins_mcp.server import get_jenkins_client
        return get_jenkins_client()

    @mcp.tool()
    async def get_job_downstream_projects(job_name: str):
        """获取job配置的下游任务列表

        参数:
            job_name: Job名称
        """
        return await tools.plugins_management.downstream_buildview.get_job_downstream_projects(get_jk(), job_name)

    @mcp.tool()
    async def get_job_upstream_projects(job_name: str):
        """获取job配置的上游任务列表

        参数:
            job_name: Job名称
        """
        return await tools.plugins_management.downstream_buildview.get_job_upstream_projects(get_jk(), job_name)

    @mcp.tool()
    async def get_build_downstream(job_name: str, build_number: int):
        """获取某次构建触发的下游构建列表

        参数:
            job_name: Job名称
            build_number: 构建编号
        """
        return await tools.plugins_management.downstream_buildview.get_build_downstream(
            get_jk(), job_name, build_number
        )

    @mcp.tool()
    async def get_build_upstream(job_name: str, build_number: int):
        """获取某次构建的上游触发信息

        参数:
            job_name: Job名称
            build_number: 构建编号
        """
        return await tools.plugins_management.downstream_buildview.get_build_upstream(
            get_jk(), job_name, build_number
        )

    @mcp.tool()
    async def get_build_downstream_tree(job_name: str, build_number: int, max_depth: int = 5):
        """递归获取完整下游构建链路树

        参数:
            job_name: Job名称
            build_number: 构建编号
            max_depth: 最大递归深度，默认5
        """
        return await tools.plugins_management.downstream_buildview.get_build_downstream_tree(
            get_jk(), job_name, build_number, max_depth
        )

    @mcp.tool()
    async def get_build_upstream_chain(job_name: str, build_number: int, max_depth: int = 10):
        """递归获取完整上游触发链

        参数:
            job_name: Job名称
            build_number: 构建编号
            max_depth: 最大递归深度，默认10
        """
        return await tools.plugins_management.downstream_buildview.get_build_upstream_chain(
            get_jk(), job_name, build_number, max_depth
        )
