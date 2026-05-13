"""Job Config History Plugin管理工具注册"""

from mcp.server.fastmcp import FastMCP

from jenkins_mcp import tools


def register_tools(mcp: FastMCP) -> None:
    """注册Job Config History Plugin管理工具"""

    def get_jk():
        from jenkins_mcp.server import get_jenkins_client
        return get_jenkins_client()

    @mcp.tool()
    async def get_all_config_history(filter: str = 'all'):
        """获取全局配置历史

        参数:
            filter: 过滤条件，可选值: all, system, jobs, deleted
        """
        return await tools.plugins_management.job_config_history.get_all_config_history(get_jk(), filter)

    @mcp.tool()
    async def get_job_config_history(job_name: str):
        """获取指定job的配置历史记录

        参数:
            job_name: Job名称（支持多级文件夹路径，如 folder/subfolder/jobname）
        """
        return await tools.plugins_management.job_config_history.get_job_config_history(get_jk(), job_name)

    @mcp.tool()
    async def get_node_config_history(node_name: str):
        """获取指定node的配置历史记录

        参数:
            node_name: Node/Agent名称
        """
        return await tools.plugins_management.job_config_history.get_node_config_history(get_jk(), node_name)

    @mcp.tool()
    async def get_config_file_content(job_name: str, timestamp: str):
        """获取指定job的某个历史版本的配置文件内容

        参数:
            job_name: Job名称
            timestamp: 历史版本时间戳（格式如 2024-01-15_10-30-00）
        """
        return await tools.plugins_management.job_config_history.get_config_file_content(
            get_jk(), job_name, timestamp
        )

    @mcp.tool()
    async def restore_job_config(job_name: str, timestamp: str):
        """回退job配置到指定历史版本

        参数:
            job_name: Job名称
            timestamp: 要回退到的历史版本时间戳
        """
        return await tools.plugins_management.job_config_history.restore_job_config(get_jk(), job_name, timestamp)

    @mcp.tool()
    async def restore_node_config(node_name: str, timestamp: str):
        """回退node配置到指定历史版本

        参数:
            node_name: Node/Agent名称
            timestamp: 要回退到的历史版本时间戳
        """
        return await tools.plugins_management.job_config_history.restore_node_config(get_jk(), node_name, timestamp)

    @mcp.tool()
    async def delete_job_config_revision(job_name: str, timestamp: str):
        """删除job的某个历史版本

        参数:
            job_name: Job名称
            timestamp: 要删除的历史版本时间戳
        """
        return await tools.plugins_management.job_config_history.delete_job_config_revision(
            get_jk(), job_name, timestamp
        )

    @mcp.tool()
    async def delete_node_config_revision(node_name: str, timestamp: str):
        """删除node的某个历史版本

        参数:
            node_name: Node/Agent名称
            timestamp: 要删除的历史版本时间戳
        """
        return await tools.plugins_management.job_config_history.delete_node_config_revision(
            get_jk(), node_name, timestamp
        )

    @mcp.tool()
    async def restore_deleted_job(job_name: str):
        """恢复已删除的job

        参数:
            job_name: 要恢复的已删除Job名称
        """
        return await tools.plugins_management.job_config_history.restore_deleted_job(get_jk(), job_name)

    @mcp.tool()
    async def get_config_diff(job_name: str, timestamp1: str, timestamp2: str):
        """对比两个历史版本的配置差异

        参数:
            job_name: Job名称
            timestamp1: 旧版本时间戳
            timestamp2: 新版本时间戳
        """
        return await tools.plugins_management.job_config_history.get_config_diff(
            get_jk(), job_name, timestamp1, timestamp2
        )
