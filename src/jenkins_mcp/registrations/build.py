"""Build管理工具注册"""

from mcp.server.fastmcp import FastMCP

from jenkins_mcp import tools


def register_tools(mcp: FastMCP) -> None:
    """注册Build管理工具"""
    
    def get_jk():
        from jenkins_mcp.server import get_jenkins_client
        return get_jenkins_client()

    @mcp.tool()
    async def get_build(name: str, number: int, depth: int = 0):
        """获取Build信息"""
        return await tools.build.get_build(get_jk(), name, number, depth)

    @mcp.tool()
    async def get_build_console_output(name: str, number: int, offset: int = 0, limit: int = None):
        """获取构建日志"""
        return await tools.build.get_build_console_output(get_jk(), name, number, offset, limit)

    @mcp.tool()
    async def get_running_builds():
        """获取运行中的Build"""
        return await tools.build.get_running_builds(get_jk())

    @mcp.tool()
    async def stop_build(name: str, number: int):
        """停止Build"""
        return await tools.build.stop_build(get_jk(), name, number)

    @mcp.tool()
    async def delete_build(name: str, number: int):
        """删除Build记录"""
        return await tools.build.delete_build(get_jk(), name, number)

    @mcp.tool()
    async def stop_all_builds(name: str = None):
        """停止所有运行中的Build"""
        return await tools.build.stop_all_builds(get_jk(), name)

    @mcp.tool()
    async def get_build_artifacts(name: str, number: int):
        """获取Build的所有归档制品列表"""
        return await tools.build.get_build_artifacts(get_jk(), name, number)

    @mcp.tool()
    async def get_build_artifact(name: str, number: int, artifact: str):
        """获取Build制品内容（文本）"""
        return await tools.build.get_build_artifact(get_jk(), name, number, artifact)

    @mcp.tool()
    async def download_build_artifact(name: str, number: int, artifact: str, path: str):
        """下载Build特定制品到本地文件"""
        return await tools.build.download_build_artifact(get_jk(), name, number, artifact, path)

    @mcp.tool()
    async def download_all_artifacts(name: str, number: int, output_dir: str):
        """下载Build的所有制品到本地目录"""
        return await tools.build.download_all_artifacts(get_jk(), name, number, output_dir)