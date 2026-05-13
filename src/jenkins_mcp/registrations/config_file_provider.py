"""Config File Provider Plugin管理工具注册"""

from mcp.server.fastmcp import FastMCP

from jenkins_mcp import tools


def register_tools(mcp: FastMCP) -> None:
    """注册Config File Provider Plugin管理工具"""

    def get_jk():
        from jenkins_mcp.server import get_jenkins_client
        return get_jenkins_client()

    @mcp.tool()
    async def get_all_config_files():
        """获取所有配置文件列表"""
        return await tools.plugins_management.config_file_provider.get_all_config_files(get_jk())

    @mcp.tool()
    async def get_config_file(config_id: str):
        """获取指定配置文件详情（含文件内容）"""
        return await tools.plugins_management.config_file_provider.get_config_file(get_jk(), config_id)

    @mcp.tool()
    async def add_config_file(
        name: str,
        content: str,
        comment: str = '',
        config_id: str = '',
        provider_id: str = 'org.jenkinsci.plugins.configfiles.custom.CustomConfig$CustomConfigProvider'
    ):
        """添加文件配置

        参数:
            name: 文件配置名称
            content: 文件内容
            comment: 可选，备注说明
            config_id: 可选，配置ID（不指定则自动生成）
            provider_id: 可选，文件提供者类型ID，不指定则使用Custom文件类型。
                可通过 get_all_config_providers 查看所有可用的provider_id。
        """
        return await tools.plugins_management.config_file_provider.add_config_file(
            get_jk(), name, content, comment, config_id, provider_id
        )

    @mcp.tool()
    async def update_config_file(config_id: str, name: str, content: str, comment: str = ''):
        """更新配置文件

        参数:
            config_id: 配置ID
            name: 文件配置名称
            content: 文件内容
            comment: 可选，备注说明
        """
        return await tools.plugins_management.config_file_provider.update_config_file(
            get_jk(), config_id, name, content, comment
        )

    @mcp.tool()
    async def delete_config_file(config_id: str):
        """删除指定配置文件"""
        return await tools.plugins_management.config_file_provider.delete_config_file(get_jk(), config_id)

    @mcp.tool()
    async def get_all_config_providers():
        """获取所有可用的文件提供者类型"""
        return await tools.plugins_management.config_file_provider.get_all_config_providers(get_jk())

    @mcp.tool()
    async def get_config_files_by_provider(provider_id: str):
        """按提供者类型获取配置文件列表"""
        return await tools.plugins_management.config_file_provider.get_config_files_by_provider(
            get_jk(), provider_id
        )
