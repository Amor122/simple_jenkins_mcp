"""Lockable Resources Plugin管理工具注册"""

from mcp.server.fastmcp import FastMCP

from jenkins_mcp import tools


def register_tools(mcp: FastMCP) -> None:
    """注册Lockable Resources Plugin管理工具"""
    
    def get_jk():
        from jenkins_mcp.server import get_jenkins_client
        return get_jenkins_client()

    @mcp.tool()
    async def get_all_lockable_resources():
        """获取所有锁资源"""
        return await tools.plugins_management.lockable_resources.get_all_lockable_resources(get_jk())

    @mcp.tool()
    async def get_lockable_resource(name: str):
        """获取指定锁资源详情"""
        return await tools.plugins_management.lockable_resources.get_lockable_resource(get_jk(), name)

    @mcp.tool()
    async def add_lockable_resource(name: str, labels: str = '', description: str = '', properties: dict = None):
        """添加锁资源
        
        参数:
            name: 资源名称
            labels: 可选，资源标签（多个用空格分隔）
            description: 可选，资源描述
            properties: 可选，键值对属性，如 {"key1": "value1", "key2": "value2"}
        """
        return await tools.plugins_management.lockable_resources.add_lockable_resource(
            get_jk(), name, labels, description, properties=properties
        )

    @mcp.tool()
    async def delete_lockable_resource(name: str):
        """删除指定锁资源"""
        return await tools.plugins_management.lockable_resources.delete_lockable_resource(get_jk(), name)

    @mcp.tool()
    async def unlock_lockable_resource(name: str):
        """解锁指定锁资源"""
        return await tools.plugins_management.lockable_resources.unlock_lockable_resource(get_jk(), name)

    @mcp.tool()
    async def reserve_lockable_resource(name: str, user: str = 'admin', reason: str = ''):
        """预留指定锁资源"""
        return await tools.plugins_management.lockable_resources.reserve_lockable_resource(
            get_jk(), name, user, reason
        )

    @mcp.tool()
    async def unreserve_lockable_resource(name: str):
        """取消预留指定锁资源"""
        return await tools.plugins_management.lockable_resources.unreserve_lockable_resource(get_jk(), name)

    @mcp.tool()
    async def get_lockable_queue():
        """获取锁资源队列信息"""
        return await tools.plugins_management.lockable_resources.get_lockable_queue(get_jk())

    @mcp.tool()
    async def lockable_resource_exists(name: str):
        """检查锁资源是否存在"""
        return await tools.plugins_management.lockable_resources.lockable_resource_exists(get_jk(), name)

    @mcp.tool()
    async def set_lockable_resource_properties(name: str, properties: dict):
        """设置锁资源的属性（替换所有属性）"""
        return await tools.plugins_management.lockable_resources.set_lockable_resource_properties(
            get_jk(), name, properties
        )

    @mcp.tool()
    async def set_lockable_resource_property(name: str, key: str, value: str):
        """设置锁资源的单个属性"""
        return await tools.plugins_management.lockable_resources.set_lockable_resource_property(
            get_jk(), name, key, value
        )

    @mcp.tool()
    async def get_lockable_resource_property(name: str, key: str):
        """获取锁资源的单个属性值"""
        return await tools.plugins_management.lockable_resources.get_lockable_resource_property(
            get_jk(), name, key
        )

    @mcp.tool()
    async def get_all_lockable_labels():
        """获取所有锁资源标签"""
        return await tools.plugins_management.lockable_resources.get_all_lockable_labels(get_jk())

    @mcp.tool()
    async def get_lockable_resources_by_label(label: str):
        """获取具有指定标签的所有锁资源"""
        return await tools.plugins_management.lockable_resources.get_lockable_resources_by_label(get_jk(), label)