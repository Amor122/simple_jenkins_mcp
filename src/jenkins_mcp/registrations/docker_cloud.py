"""Docker Cloud Plugin管理工具注册"""

from mcp.server.fastmcp import FastMCP

from jenkins_mcp import tools


def register_tools(mcp: FastMCP) -> None:
    """注册Docker Cloud Plugin管理工具"""

    def get_jk():
        from jenkins_mcp.server import get_jenkins_client
        return get_jenkins_client()

    @mcp.tool()
    async def get_docker_clouds():
        """获取所有Docker云配置列表"""
        return await tools.plugins_management.docker_cloud.get_docker_clouds(get_jk())

    @mcp.tool()
    async def get_docker_cloud(cloud_name: str):
        """获取指定Docker云配置详情"""
        return await tools.plugins_management.docker_cloud.get_docker_cloud(get_jk(), cloud_name)

    @mcp.tool()
    async def create_docker_cloud(name: str, server_url: str, credentials_id: str = '',
                                  container_cap: int = 100, connect_timeout: int = 5, read_timeout: int = 15):
        """创建Docker云配置"""
        return await tools.plugins_management.docker_cloud.create_docker_cloud(
            get_jk(), name, server_url, credentials_id, container_cap, connect_timeout, read_timeout
        )

    @mcp.tool()
    async def delete_docker_cloud(cloud_name: str):
        """删除Docker云配置"""
        return await tools.plugins_management.docker_cloud.delete_docker_cloud(get_jk(), cloud_name)

    @mcp.tool()
    async def get_docker_templates(cloud_name: str):
        """获取Docker云的所有模板列表"""
        return await tools.plugins_management.docker_cloud.get_docker_templates(get_jk(), cloud_name)

    @mcp.tool()
    async def get_docker_template(cloud_name: str, template_name: str):
        """获取Docker云中指定模板详情"""
        return await tools.plugins_management.docker_cloud.get_docker_template(get_jk(), cloud_name, template_name)

    @mcp.tool()
    async def add_docker_template(cloud_name: str, template_config: dict):
        """添加Docker模板到云

        参数:
            cloud_name: Docker云名称
            template_config: 模板配置，包含name, image(必填), label, instanceCap, privileged等
        """
        return await tools.plugins_management.docker_cloud.add_docker_template(
            get_jk(), cloud_name, template_config
        )

    @mcp.tool()
    async def update_docker_template(cloud_name: str, template_name: str, template_config: dict):
        """更新Docker模板"""
        return await tools.plugins_management.docker_cloud.update_docker_template(
            get_jk(), cloud_name, template_name, template_config
        )

    @mcp.tool()
    async def delete_docker_template(cloud_name: str, template_name: str):
        """删除Docker云中的模板"""
        return await tools.plugins_management.docker_cloud.delete_docker_template(
            get_jk(), cloud_name, template_name
        )

    @mcp.tool()
    async def copy_docker_template(cloud_name: str, source_template_name: str, new_template_name: str):
        """复制Docker模板"""
        return await tools.plugins_management.docker_cloud.copy_docker_template(
            get_jk(), cloud_name, source_template_name, new_template_name
        )
