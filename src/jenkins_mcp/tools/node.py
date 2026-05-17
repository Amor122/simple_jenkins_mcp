"""
Jenkins MCP Server - Node管理工具模块

基于python-jenkins的实现
"""

from typing import Optional
from jenkins_mcp.tools.utils import admin_only, write_only


# ==================== Node管理工具 ====================

async def get_all_nodes(jk, depth: int = 0) -> list:
    """获取所有节点"""
    return jk.get_nodes(depth=depth)


async def get_node(jk, name: str, depth: int = 2) -> dict:
    """获取节点详情"""
    return jk.get_node_info(name, depth=depth)


async def get_node_config(jk, name: str) -> str:
    """获取节点配置XML"""
    if name in ['Built-In Node', '(master)', 'master']:
        raise PermissionError("Built-In Node不支持获取配置XML")
    return jk.get_node_config(name)


@write_only
async def set_node_config(jk, name: str, config_xml: str) -> dict:
    """设置节点配置"""
    jk.reconfig_node(name, config_xml)
    return {"status": "success", "node": name}


@admin_only
async def create_node(jk, name: str, config_xml: str) -> dict:
    """创建节点

    参数:
        name: 节点名称
        config_xml: 节点配置XML（定义启动方式、远程目录等）
    """
    jk.create_node(name, config_xml=config_xml)
    return {"status": "created", "node": name}


@admin_only
async def delete_node(jk, name: str) -> dict:
    """删除节点"""
    jk.delete_node(name)
    return {"status": "deleted", "node": name}


@write_only
async def set_node_offline(jk, name: str, message: str = "") -> dict:
    """设置节点离线"""
    jk.disable_node(name, message)
    return {"status": "offline", "node": name}


@write_only
async def set_node_online(jk, name: str) -> dict:
    """设置节点在线"""
    jk.enable_node(name)
    return {"status": "online", "node": name}


async def node_exists(jk, name: str) -> bool:
    """检查节点是否存在"""
    return jk.node_exists(name)