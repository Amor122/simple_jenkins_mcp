"""
Jenkins MCP Server - Script执行工具模块

提供Groovy脚本执行功能，用于访问Jenkins内部API
"""

from jenkins_mcp.tools.utils import write_only


@write_only
async def run_groovy_script(jk, script: str, node: str = None) -> str:
    """执行任意Groovy脚本
    
    用于访问Jenkins没有REST API的内部功能
    
    参数:
        jk: Jenkins客户端
        script: Groovy脚本代码
        node: 可选，在指定节点上执行（默认在master）
    
    返回:
        脚本执行结果
    """
    if node:
        return jk.run_script(script, node)
    return jk.run_script(script)


@write_only
async def get_jenkins_info(jk) -> dict:
    """获取Jenkins系统信息
    
    返回:
        Jenkins系统信息
    """
    return jk.get_info()


@write_only
async def get_jenkins_version(jk) -> str:
    """获取Jenkins版本
    
    返回:
        Jenkins版本号
    """
    return jk.get_version()


@write_only
async def get_whoami(jk) -> dict:
    """获取当前认证用户信息
    
    返回:
        当前用户信息
    """
    return jk.get_whoami()