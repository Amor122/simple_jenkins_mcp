"""
Jenkins MCP Server - Job管理工具模块

基于python-jenkins的实现
"""

from typing import Optional, Set
from jenkins_mcp.tools.utils import check_read_only


# 工具定义
def define_job_tool(tags: frozenset):
    """Job工具装饰器"""
    def decorator(func):
        @property
        def wrapper(self):
            check_read_only(tags)
            return func
        return wrapper
    return decorator


# ==================== Job管理工具 ====================

async def get_all_jobs(jk, folder_depth: Optional[int] = None) -> list:
    """
    获取所有Job列表
    
    支持文件夹嵌套查询，可指定查询深度
    
    参数:
        folder_depth: 文件夹最大深度，None表示无限制
    
    返回:
        Job列表
    """
    return jk.get_all_jobs(folder_depth=folder_depth)


async def get_job(jk, name: str, depth: int = 0) -> dict:
    """
    获取指定Job信息
    
    参数:
        name: Job名称（支持文件夹路径，如 folder/job）
        depth: JSON深度
    
    返回:
        Job信息字典
    """
    return jk.get_job_info(name, depth=depth)


async def get_job_config(jk, name: str) -> str:
    """
    获取Job配置XML
    
    参数:
        name: Job名称
    
    返回:
        XML配置字符串
    """
    return jk.get_job_config(name)


async def set_job_config(jk, name: str, config_xml: str) -> dict:
    """
    设置Job配置
    
    参数:
        name: Job名称
        config_xml: XML配置
    
    返回:
        执行结果
    """
    jk.reconfig_job(name, config_xml)
    return {"status": "success", "job": name}


async def create_job(jk, name: str, config_xml: str) -> dict:
    """
    创建新Job
    
    参数:
        name: Job名称
        config_xml: XML配置
    
    返回:
        执行结果
    """
    jk.create_job(name, config_xml)
    return {"status": "created", "job": name}


async def delete_job(jk, name: str) -> dict:
    """
    删除Job
    
    参数:
        name: Job名称
    
    返回:
        执行结果
    """
    jk.delete_job(name)
    return {"status": "deleted", "job": name}


async def copy_job(jk, from_name: str, to_name: str) -> dict:
    """
    复制Job
    
    参数:
        from_name: 源Job名称
        to_name: 目标Job名称
    
    返回:
        执行结果
    """
    jk.copy_job(from_name, to_name)
    return {"status": "copied", "from": from_name, "to": to_name}


async def rename_job(jk, name: str, new_name: str) -> dict:
    """
    重命名Job
    
    参数:
        name: 原Job名称
        new_name: 新Job名称
    
    返回:
        执行结果
    """
    jk.rename_job(name, new_name)
    return {"status": "renamed", "from": name, "to": new_name}


async def enable_job(jk, name: str) -> dict:
    """
    启用Job
    
    参数:
        name: Job名称
    
    返回:
        执行结果
    """
    jk.enable_job(name)
    return {"status": "enabled", "job": name}


async def disable_job(jk, name: str) -> dict:
    """
    禁用Job
    
    参数:
        name: Job名称
    
    返回:
        执行结果
    """
    jk.disable_job(name)
    return {"status": "disabled", "job": name}


async def build_job(
    jk, 
    name: str, 
    parameters: Optional[dict] = None,
    token: Optional[str] = None
) -> int:
    """
    触发Job构建
    
    参数:
        name: Job名称
        parameters: 构建参数（可选）
        token: API Token（可选）
    
    返回:
        队列ID
    """
    return jk.build_job(name, parameters, token)


async def set_next_build_number(jk, name: str, number: int) -> dict:
    """
    设置下一个构建号
    
    参数:
        name: Job名称
        number: 构建号
    
    返回:
        执行结果
    """
    jk.set_next_build_number(name, number)
    return {"status": "success", "job": name, "next_build_number": number}


async def wipeout_workspace(jk, name: str) -> dict:
    """
    清空工作区
    
    参数:
        name: Job名称
    
    返回:
        执行结果
    """
    jk.wipeout_job_workspace(name)
    return {"status": "wiped", "job": name}


async def job_exists(jk, name: str) -> bool:
    """
    检查Job是否存在
    
    参数:
        name: Job名称
    
    返回:
        是否存在
    """
    return jk.job_exists(name)


async def check_jenkinsfile_syntax(jk, jenkinsfile: str) -> list:
    """
    检查Pipeline语法
    
    参数:
        jenkinsfile: Jenkinsfile内容
    
    返回:
        错误列表
    """
    return jk.check_jenkinsfile_syntax(jenkinsfile)