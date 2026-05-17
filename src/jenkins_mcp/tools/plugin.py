"""
Jenkins MCP Server - Plugin管理工具模块
"""

from typing import Optional
from jenkins_mcp.tools.utils import write_only


async def get_all_plugins(jk, depth: int = 2) -> list:
    """获取所有安装的插件"""
    return jk.get_plugins(depth=depth)


async def get_plugin(jk, short_name: str, depth: int = 2) -> dict:
    """获取指定插件详情"""
    return jk.get_plugin_info(short_name, depth=depth)


async def get_plugins_with_problems(jk) -> list:
    """获取有问题的插件"""
    plugins = jk.get_plugins(depth=2)
    jenkins_version = jk.get_version()
    problems = []
    installed = {p['shortName']: p for p in plugins}
    
    for plugin in plugins:
        short_name = plugin.get('shortName', '')
        version = plugin.get('version', '')
        required_core = plugin.get('requiredCoreVersion', '')
        
        if required_core and jenkins_version:
            core_parts = [int(p) for p in jenkins_version.split('.')[:3]]
            required_parts = [int(p) for p in required_core.split('.')[:3]]
            if core_parts < required_parts:
                problems.append({
                    'shortName': short_name,
                    'problem': 'incompatible_core_version',
                    'pluginVersion': version,
                    'requiredCoreVersion': required_core,
                    'jenkinsVersion': jenkins_version,
                    'severity': 'error'
                })
        
        if not plugin.get('enabled'):
            problems.append({
                'shortName': short_name,
                'problem': 'plugin_disabled',
                'severity': 'warning'
            })
    
    return problems


@write_only
async def install_plugin(jk, short_name: str, version: Optional[str] = None) -> dict:
    """安装插件

    参数:
        short_name: 插件短名称 (如 "git")
        version: 可选，指定版本（不指定则安装最新版）
    """
    return jk.install_plugin(short_name, version)


@write_only
async def enable_plugin(jk, short_name: str) -> dict:
    """启用插件"""
    jk.enable_plugin(short_name)
    return {"status": "enabled", "plugin": short_name}


@write_only
async def disable_plugin(jk, short_name: str) -> dict:
    """禁用插件"""
    jk.disable_plugin(short_name)
    return {"status": "disabled", "plugin": short_name}


@write_only
async def uninstall_plugin(jk, short_name: str) -> dict:
    """卸载插件"""
    jk.uninstall_plugin(short_name)
    return {"status": "uninstalled", "plugin": short_name}