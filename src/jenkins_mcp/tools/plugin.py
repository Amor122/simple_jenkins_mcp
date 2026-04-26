"""
Jenkins MCP Server - Plugin管理工具模块

基于python-jenkins的实现
"""

import os

def check_read_only(tags) -> None:
    read_only = os.getenv('JENKINS_READ_ONLY', 'false').lower() == 'true'
    if read_only and tags != frozenset({'read'}):
        raise PermissionError("只读模式下禁止此操作")


async def get_all_plugins(jk, depth: int = 2) -> list:
    """获取所有安装的插件"""
    check_read_only({'read'})
    return jk.get_plugins(depth=depth)


async def get_plugin(jk, short_name: str, depth: int = 2) -> dict:
    """获取指定插件详情"""
    check_read_only({'read'})
    return jk.get_plugin_info(short_name, depth=depth)


async def get_plugins_with_problems(jk) -> list:
    """获取有问题的插件"""
    check_read_only({'read'})
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