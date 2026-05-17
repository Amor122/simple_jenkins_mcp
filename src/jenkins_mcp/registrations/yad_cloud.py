"""Yet Another Docker Cloud Plugin管理工具注册"""

from mcp.server.fastmcp import FastMCP

from jenkins_mcp import tools


def register_tools(mcp: FastMCP) -> None:
    """注册YAD Cloud Plugin管理工具"""

    def get_jk():
        from jenkins_mcp.server import get_jenkins_client
        return get_jenkins_client()

    @mcp.tool()
    async def get_yad_clouds():
        """获取所有YAD云配置列表"""
        return await tools.plugins_management.yad_cloud.get_yad_clouds(get_jk())

    @mcp.tool()
    async def get_yad_cloud(cloud_name: str):
        """获取指定YAD云配置详情"""
        return await tools.plugins_management.yad_cloud.get_yad_cloud(get_jk(), cloud_name)

    @mcp.tool()
    async def create_yad_cloud(name: str, server_url: str, credentials_id: str = '',
                               container_cap: int = 50, connect_timeout: int = 0, read_timeout: int = 0):
        """创建YAD云配置"""
        return await tools.plugins_management.yad_cloud.create_yad_cloud(
            get_jk(), name, server_url, credentials_id, container_cap, connect_timeout, read_timeout
        )

    @mcp.tool()
    async def delete_yad_cloud(cloud_name: str):
        """删除YAD云配置"""
        return await tools.plugins_management.yad_cloud.delete_yad_cloud(get_jk(), cloud_name)

    @mcp.tool()
    async def get_yad_templates(cloud_name: str):
        """获取YAD云的所有模板列表"""
        return await tools.plugins_management.yad_cloud.get_yad_templates(get_jk(), cloud_name)

    @mcp.tool()
    async def get_yad_template(cloud_name: str, template_id: str):
        """获取YAD云中指定模板详情"""
        return await tools.plugins_management.yad_cloud.get_yad_template(get_jk(), cloud_name, template_id)

    @mcp.tool()
    async def add_yad_template(cloud_name: str, template_config: dict):
        """添加YAD模板到云

        参数:
            cloud_name: YAD云名称
            template_config: 模板配置，包含image(必填), label, remoteFs, numExecutors等
        """
        return await tools.plugins_management.yad_cloud.add_yad_template(
            get_jk(), cloud_name, template_config
        )

    @mcp.tool()
    async def delete_yad_template(cloud_name: str, template_id: str):
        """删除YAD云中的模板"""
        return await tools.plugins_management.yad_cloud.delete_yad_template(
            get_jk(), cloud_name, template_id
        )

    @mcp.tool()
    async def update_yad_template(cloud_name: str, template_id: str, template_config: dict):
        """更新YAD模板

        参数:
            cloud_name: YAD云名称
            template_id: 模板ID或标签
            template_config: 需要更新的字段，包含label, remoteFs, image, command, privileged等
        """
        return await tools.plugins_management.yad_cloud.update_yad_template(
            get_jk(), cloud_name, template_id, template_config
        )

    @mcp.tool()
    async def copy_yad_template(cloud_name: str, source_template_id: str, new_label: str):
        """复制YAD模板"""
        return await tools.plugins_management.yad_cloud.copy_yad_template(
            get_jk(), cloud_name, source_template_id, new_label
        )
