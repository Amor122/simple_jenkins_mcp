"""Kubernetes Cloud Plugin管理工具注册"""

from mcp.server.fastmcp import FastMCP

from jenkins_mcp import tools


def register_tools(mcp: FastMCP) -> None:
    """注册Kubernetes Cloud Plugin管理工具"""

    def get_jk():
        from jenkins_mcp.server import get_jenkins_client
        return get_jenkins_client()

    @mcp.tool()
    async def get_kubernetes_clouds():
        """获取所有Kubernetes云配置列表"""
        return await tools.plugins_management.kubernetes_cloud.get_kubernetes_clouds(get_jk())

    @mcp.tool()
    async def get_kubernetes_cloud(cloud_name: str):
        """获取指定Kubernetes云配置详情"""
        return await tools.plugins_management.kubernetes_cloud.get_kubernetes_cloud(get_jk(), cloud_name)

    @mcp.tool()
    async def create_kubernetes_cloud(name: str, server_url: str, namespace: str = 'default',
                                      credentials_id: str = '', container_cap: int = 0,
                                      skip_tls_verify: bool = False, jenkins_url: str = '',
                                      web_socket: bool = False):
        """创建Kubernetes云配置"""
        return await tools.plugins_management.kubernetes_cloud.create_kubernetes_cloud(
            get_jk(), name, server_url, namespace, credentials_id, container_cap,
            skip_tls_verify, jenkins_url, web_socket
        )

    @mcp.tool()
    async def delete_kubernetes_cloud(cloud_name: str):
        """删除Kubernetes云配置"""
        return await tools.plugins_management.kubernetes_cloud.delete_kubernetes_cloud(get_jk(), cloud_name)

    @mcp.tool()
    async def get_pod_templates(cloud_name: str):
        """获取Kubernetes云的所有Pod模板列表"""
        return await tools.plugins_management.kubernetes_cloud.get_pod_templates(get_jk(), cloud_name)

    @mcp.tool()
    async def get_pod_template(cloud_name: str, template_name: str):
        """获取指定Pod模板详情"""
        return await tools.plugins_management.kubernetes_cloud.get_pod_template(get_jk(), cloud_name, template_name)

    @mcp.tool()
    async def add_pod_template(cloud_name: str, template_config: dict):
        """添加Pod模板到Kubernetes云

        参数:
            cloud_name: Kubernetes云名称
            template_config: 模板配置，包含name(必填), containers(必填), label, yaml等
        """
        return await tools.plugins_management.kubernetes_cloud.add_pod_template(
            get_jk(), cloud_name, template_config
        )

    @mcp.tool()
    async def delete_pod_template(cloud_name: str, template_name: str):
        """删除Kubernetes云中的Pod模板"""
        return await tools.plugins_management.kubernetes_cloud.delete_pod_template(
            get_jk(), cloud_name, template_name
        )

    @mcp.tool()
    async def copy_pod_template(cloud_name: str, source_template_name: str, new_template_name: str):
        """复制Kubernetes Pod模板"""
        return await tools.plugins_management.kubernetes_cloud.copy_pod_template(
            get_jk(), cloud_name, source_template_name, new_template_name
        )
