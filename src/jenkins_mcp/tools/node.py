"""
Jenkins MCP Server - Node管理工具模块

基于python-jenkins的实现
"""

import os
from typing import Optional

def check_read_only(tags) -> None:
    read_only = os.getenv('JENKINS_READ_ONLY', 'false').lower() == 'true'
    if read_only and tags != frozenset({'read'}):
        raise PermissionError("只读模式下禁止此操作")


# ==================== Node管理工具 ====================

async def get_all_nodes(jk, depth: int = 0) -> list:
    """获取所有节点"""
    check_read_only({'read'})
    return jk.get_nodes(depth=depth)


async def get_node(jk, name: str, depth: int = 2) -> dict:
    """获取节点详情"""
    check_read_only({'read'})
    return jk.get_node_info(name, depth=depth)


async def get_node_config(jk, name: str) -> str:
    """获取节点配置XML"""
    check_read_only({'read'})
    if name in ['Built-In Node', '(master)', 'master']:
        raise PermissionError("Built-In Node不支持获取配置XML")
    return jk.get_node_config(name)


async def set_node_config(jk, name: str, config_xml: str) -> dict:
    """设置节点配置"""
    check_read_only({'write'})
    jk.reconfig_node(name, config_xml)
    return {"status": "success", "node": name}


async def create_node(jk, name: str, config_xml: str) -> dict:
    """创建节点"""
    check_read_only({'admin'})
    jk.create_node(name, launcher_params={'stapler-class': 'hudson.slaves.CommandLauncher'})
    return {"status": "created", "node": name}


async def delete_node(jk, name: str) -> dict:
    """删除节点"""
    check_read_only({'admin'})
    jk.delete_node(name)
    return {"status": "deleted", "node": name}


async def set_node_offline(jk, name: str, message: str = "") -> dict:
    """设置节点离线"""
    check_read_only({'write'})
    jk.disable_node(name, message)
    return {"status": "offline", "node": name}


async def set_node_online(jk, name: str) -> dict:
    """设置节点在线"""
    check_read_only({'write'})
    jk.enable_node(name)
    return {"status": "online", "node": name}


async def node_exists(jk, name: str) -> bool:
    """检查节点是否存在"""
    check_read_only({'read'})
    return jk.node_exists(name)