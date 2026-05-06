"""Label管理工具注册"""

from mcp.server.fastmcp import FastMCP

from jenkins_mcp import tools


def register_tools(mcp: FastMCP) -> None:
    """注册Label管理工具"""
    
    def get_jk():
        from jenkins_mcp.server import get_jenkins_client
        return get_jenkins_client()

    @mcp.tool()
    async def get_all_labels(depth: int = 2):
        """获取所有Label及关联节点"""
        return await tools.label.get_all_labels(get_jk(), depth)

    @mcp.tool()
    async def get_label(name: str, depth: int = 2):
        """获取指定Label详情"""
        return await tools.label.get_label(get_jk(), name, depth)

    @mcp.tool()
    async def get_nodes_by_label(label: str, depth: int = 2):
        """获取具有指定Label的所有节点"""
        return await tools.label.get_nodes_by_label(get_jk(), label, depth)

    @mcp.tool()
    async def get_label_load():
        """获取Label负载信息"""
        return await tools.label.get_label_load(get_jk())