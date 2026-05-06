"""Cloud管理工具注册"""

from mcp.server.fastmcp import FastMCP

from jenkins_mcp import tools


def register_tools(mcp: FastMCP) -> None:
    """注册Cloud管理工具"""
    
    def get_jk():
        from jenkins_mcp.server import get_jenkins_client
        return get_jenkins_client()

    @mcp.tool()
    async def get_all_clouds():
        """获取所有云配置"""
        return await tools.cloud.get_all_clouds(get_jk())

    @mcp.tool()
    async def get_cloud_config(name: str):
        """获取指定云配置的详细信息"""
        return await tools.cloud.get_cloud_config(get_jk(), name)

    @mcp.tool()
    async def get_cloud_templates(cloud_name: str):
        """获取云的所有模板"""
        return await tools.cloud.get_cloud_templates(get_jk(), cloud_name)

    @mcp.tool()
    async def analyze_cloud_nodes(cloud_name: str = None):
        """分析云相关的节点"""
        return await tools.cloud.analyze_cloud_nodes(get_jk(), cloud_name)

    @mcp.tool()
    async def analyze_cloud_availability(cloud_name: str = None):
        """分析云可用性和健康状态"""
        return await tools.cloud.analyze_cloud_availability(get_jk(), cloud_name)

    @mcp.tool()
    async def disable_cloud(cloud_name: str):
        """禁用云"""
        return await tools.cloud.disable_cloud(get_jk(), cloud_name)

    @mcp.tool()
    async def enable_cloud(cloud_name: str):
        """启用云"""
        return await tools.cloud.enable_cloud(get_jk(), cloud_name)

    @mcp.tool()
    async def delete_cloud(cloud_name: str):
        """删除云配置"""
        return await tools.cloud.delete_cloud(get_jk(), cloud_name)

    @mcp.tool()
    async def delete_template(cloud_name: str, template_name: str):
        """删除云模板"""
        return await tools.cloud.delete_template(get_jk(), cloud_name, template_name)

    @mcp.tool()
    async def create_kubernetes_cloud(name: str, server_url: str, namespace: str = 'default',
                                   credentials_id: str = None, container_cap: int = 0):
        """创建Kubernetes云配置"""
        return await tools.cloud.create_kubernetes_cloud(
            get_jk(), name, server_url, namespace, credentials_id, container_cap
        )

    @mcp.tool()
    async def add_pod_template(cloud_name: str, template_config: dict):
        """添加Pod模板到Kubernetes云"""
        return await tools.cloud.add_pod_template(get_jk(), cloud_name, template_config)

    @mcp.tool()
    async def get_kubernetes_pods(namespace: str = None):
        """获取Kubernetes pods信息"""
        return await tools.cloud.get_kubernetes_pods(get_jk(), namespace)

    @mcp.tool()
    async def get_cloud_provisioning_stats():
        """获取云Provisioning统计"""
        return await tools.cloud.get_provisioning_stats(get_jk())