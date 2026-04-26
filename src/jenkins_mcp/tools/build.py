"""
Jenkins MCP Server - Build管理工具模块

基于python-jenkins的实现
"""

import os
from typing import Optional

# 只读模式检查
def check_read_only(tags) -> None:
    """检查只读模式"""
    read_only = os.getenv('JENKINS_READ_ONLY', 'false').lower() == 'true'
    if read_only and tags != frozenset({'read'}):
        raise PermissionError("只读模式下禁止此操作")


# ==================== Build管理工具 ====================

async def get_build(jk, name: str, number: int, depth: int = 0) -> dict:
    """
    获取Build信息
    
    参数:
        name: Job名称
        number: 构建号
        depth: JSON深度
    
    返回:
        Build信息字典
    """
    check_read_only({'read'})
    return jk.get_build_info(name, number, depth)


async def get_build_console_output(
    jk, 
    name: str, 
    number: int,
    offset: int = 0,
    limit: int = None
) -> str:
    """
    获取构建日志
    
    参数:
        name: Job名称
        number: 构建号
        offset: 起始行偏移
        limit: 最大行数（None表示全部）
    
    返回:
        日志字符串
    """
    check_read_only({'read'})
    output = jk.get_build_console_output(name, number)
    
    lines = output.split('\n')
    if offset > 0:
        lines = lines[offset:]
    if limit is not None:
        lines = lines[:limit]
    
    return '\n'.join(lines)


async def get_running_builds(jk) -> list:
    """
    获取运行中的Build列表
    
    返回:
        运行中的Build列表
    """
    check_read_only({'read'})
    return jk.get_running_builds()


async def stop_build(jk, name: str, number: int) -> dict:
    """
    停止Build
    
    参数:
        name: Job名称
        number: 构建号
    
    返回:
        执行结果
    """
    check_read_only({'write'})
    jk.stop_build(name, number)
    return {"status": "stopped", "job": name, "build_number": number}


async def delete_build(jk, name: str, number: int) -> dict:
    """
    删除Build记录
    
    参数:
        name: Job名称
        number: 构建号
    
    返回:
        执行结果
    """
    check_read_only({'write'})
    jk.delete_build(name, number)
    return {"status": "deleted", "job": name, "build_number": number}


async def stop_all_builds(jk, name: str = None) -> dict:
    """
    停止所有运行中的Build
    
    参数:
        name: Job名称（可选，为None表示所有）
    
    返回:
        停止的Build列表
    """
    check_read_only({'write'})
    running = jk.get_running_builds()
    stopped = []
    
    for build in running:
        if name is None or build.get('name') == name:
            jk.stop_build(build['name'], build['number'])
            stopped.append({
                'job': build['name'],
                'build_number': build['number']
            })
    
    return {"status": "stopped", "count": len(stopped), "builds": stopped}


async def get_build_artifacts(jk, name: str, number: int) -> list:
    """
    获取Build的所有归档制品列表
    
    参数:
        name: Job名称
        number: 构建号
    
    返回:
        制品列表 [{relativePath, displayPath, fileName}, ...]
    """
    check_read_only({'read'})
    return jk.get_build_artifacts(name, number)


async def get_build_artifact(jk, name: str, number: int, artifact: str) -> str:
    """
    获取Build制品内容（文本）
    
    参数:
        name: Job名称
        number: 构建号
        artifact: 制品相对路径 (如 "data.txt")
    
    返回:
        制品文本内容
    """
    check_read_only({'read'})
    info = jk.get_build_artifact(name, number, artifact)
    if isinstance(info, dict) and 'content' in info:
        return info['content']
    return str(info)


async def download_build_artifact(
    jk,
    name: str,
    number: int,
    artifact: str,
    path: str
) -> dict:
    """
    下载Build制品到本地文件
    
    参数:
        name: Job名称
        number: 构建号
        artifact: 制品相对路径 (如 "data.txt")
        path: 本地保存路径
    
    返回:
        {'file': path, 'size': bytes}
    """
    check_read_only({'write'})
    return jk.get_build_artifact_to_file(name, number, artifact, path)


async def download_all_artifacts(
    jk,
    name: str,
    number: int,
    output_dir: str
) -> list:
    """
    下载Build的所有制品到本地目录
    
    参数:
        name: Job名称
        number: 构建号
        output_dir: 保存目录
    
    返回:
        下载的制品列表
    """
    check_read_only({'write'})
    artifacts = jk.get_build_artifacts(name, number)
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    results = []
    for a in artifacts:
        rel_path = a['relativePath']
        filename = os.path.basename(rel_path)
        local_path = os.path.join(output_dir, filename)
        result = jk.get_build_artifact_to_file(name, number, rel_path, local_path)
        results.append(result)
    
    return results