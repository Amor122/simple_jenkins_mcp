"""
Jenkins MCP Server - View管理工具模块
"""

from typing import Optional
from jenkins_mcp.tools.utils import write_only


async def get_views(jk) -> list:
    """获取所有视图"""
    return jk.get_views()


async def view_exists(jk, name: str) -> bool:
    """检查视图是否存在"""
    return jk.view_exists(name)


async def get_view_name(jk, name: str) -> Optional[str]:
    """获取视图名称（验证视图存在性）"""
    return jk.get_view_name(name)


@write_only
async def create_view(jk, name: str, config_xml: str) -> dict:
    """创建视图"""
    jk.create_view(name, config_xml)
    return {"status": "created", "view": name}


async def get_view_config(jk, name: str) -> str:
    """获取视图配置XML"""
    return jk.get_view_config(name)


@write_only
async def reconfig_view(jk, name: str, config_xml: str) -> dict:
    """更新视图配置"""
    jk.reconfig_view(name, config_xml)
    return {"status": "updated", "view": name}


@write_only
async def delete_view(jk, name: str) -> dict:
    """删除视图"""
    jk.delete_view(name)
    return {"status": "deleted", "view": name}
