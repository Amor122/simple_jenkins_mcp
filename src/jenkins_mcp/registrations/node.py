"""Node管理工具注册"""

from mcp.server.fastmcp import FastMCP

from jenkins_mcp import tools
from jenkins_mcp.registrations.helpers import register_tool


def register_tools(mcp: FastMCP) -> None:
    """注册Node管理工具"""
    
    def get_jk():
        from jenkins_mcp.server import get_jenkins_client
        return get_jenkins_client()

    @mcp.tool()
    async def get_all_nodes(depth: int = 0):
        """获取所有节点"""
        return await tools.node.get_all_nodes(get_jk(), depth)

    @mcp.tool()
    async def get_node(name: str, depth: int = 2):
        """获取节点详情"""
        return await tools.node.get_node(get_jk(), name, depth)

    @mcp.tool()
    async def get_node_config(name: str):
        """获取节点配置"""
        return await tools.node.get_node_config(get_jk(), name)

    @register_tool(mcp, write_only=True)
    async def set_node_config(name: str, config_xml: str):
        """设置节点配置"""
        return await tools.node.set_node_config(get_jk(), name, config_xml)

    @register_tool(mcp, write_only=True)
    async def create_node(name: str, config_xml: str):
        """创建节点"""
        return await tools.node.create_node(get_jk(), name, config_xml)

    @register_tool(mcp, write_only=True)
    async def delete_node(name: str):
        """删除节点"""
        return await tools.node.delete_node(get_jk(), name)

    @register_tool(mcp, write_only=True)
    async def set_node_offline(name: str, message: str = ''):
        """设置节点离线"""
        return await tools.node.set_node_offline(get_jk(), name, message)

    @register_tool(mcp, write_only=True)
    async def set_node_online(name: str):
        """设置节点在线"""
        return await tools.node.set_node_online(get_jk(), name)

    @mcp.tool()
    async def node_exists(name: str):
        """检查节点是否存在"""
        return await tools.node.node_exists(get_jk(), name)