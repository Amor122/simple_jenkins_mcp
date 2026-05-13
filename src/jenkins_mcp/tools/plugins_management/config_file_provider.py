"""
Config File Provider Plugin管理模块

支持对Jenkins config-file-provider-plugin的管理:
- 查看已配置的文件列表
- 查看某个文件配置详情
- 添加文件配置
- 更新文件配置
- 删除文件配置
- 查看所有文件提供者类型
- 按提供者类型筛选文件
"""

import base64
import json
from typing import Optional

from jenkins_mcp.jenkins import Jenkins


async def get_all_config_files(jk: Jenkins) -> list:
    """获取所有已配置的文件列表"""
    script = '''
import groovy.json.JsonOutput
import org.jenkinsci.plugins.configfiles.GlobalConfigFiles

def store = GlobalConfigFiles.get()
def result = store.getConfigs().collect { c ->
    [
        id: c.id,
        name: c.name,
        comment: c.comment,
        providerId: c.providerId
    ]
}
return JsonOutput.toJson(result)
'''
    result = jk.run_script(script)
    if result:
        try:
            return json.loads(result)
        except:
            return [{'error': 'Failed to parse result', 'raw': result}]
    return []


async def get_config_file(jk: Jenkins, config_id: str) -> Optional[dict]:
    """获取指定文件配置的详情（含文件内容）"""
    script = f'''
import groovy.json.JsonOutput
import org.jenkinsci.plugins.configfiles.GlobalConfigFiles

def store = GlobalConfigFiles.get()
def c = store.getById("{config_id}")
if (c == null) return "null"
return JsonOutput.toJson([id: c.id, name: c.name, comment: c.comment, content: c.content, providerId: c.providerId])
'''
    result = jk.run_script(script)
    if result:
        try:
            parsed = json.loads(result)
            return parsed if parsed else None
        except:
            return {'error': 'Failed to parse result', 'raw': result}
    return None


async def add_config_file(
    jk: Jenkins,
    name: str,
    content: str,
    comment: str = '',
    config_id: str = '',
    provider_id: str = 'org.jenkinsci.plugins.configfiles.custom.CustomConfig$CustomConfigProvider'
) -> dict:
    """添加文件配置

    参数:
        name: 文件配置名称
        content: 文件内容
        comment: 可选，备注说明
        config_id: 可选，配置ID（不指定则自动生成）
        provider_id: 可选，文件提供者类型ID（默认Custom文件）
    """
    content_b64 = base64.b64encode(content.encode('utf-8')).decode('utf-8')
    comment = comment or ''

    script = f'''
import groovy.json.JsonOutput
import org.jenkinsci.plugins.configfiles.GlobalConfigFiles
import org.jenkinsci.lib.configprovider.ConfigProvider

def store = GlobalConfigFiles.get()

def provider = ConfigProvider.getByIdOrNull("{provider_id}")
if (provider == null) {{
    return JsonOutput.toJson([success: false, error: "Provider not found: {provider_id}"])
}}

def configId = "{config_id}"
if (configId == null || configId.isEmpty()) {{
    configId = provider.providerId + "." + System.currentTimeMillis()
}}

def existing = store.getById(configId)
if (existing != null) {{
    return JsonOutput.toJson([success: false, error: "Config already exists: " + configId])
}}

def decoded = new String("{content_b64}".decodeBase64())
def config = provider.newConfig(configId, "{name}", "{comment}", decoded)
store.save(config)
return JsonOutput.toJson([success: true, id: configId])
'''
    result = jk.run_script(script)
    try:
        return json.loads(result)
    except:
        return {'success': True, 'id': config_id or 'auto', 'raw': result}


async def update_config_file(
    jk: Jenkins,
    config_id: str,
    name: str,
    content: str,
    comment: str = ''
) -> dict:
    """更新文件配置

    参数:
        config_id: 配置ID
        name: 文件配置名称
        content: 文件内容
        comment: 可选，备注说明
    """
    content_b64 = base64.b64encode(content.encode('utf-8')).decode('utf-8')
    comment = comment or ''

    script = f'''
import groovy.json.JsonOutput
import org.jenkinsci.plugins.configfiles.GlobalConfigFiles
import org.jenkinsci.lib.configprovider.ConfigProvider

def store = GlobalConfigFiles.get()
def existing = store.getById("{config_id}")
if (existing == null) {{
    return JsonOutput.toJson([success: false, error: "Config not found: {config_id}"])
}}

def provider = ConfigProvider.getByIdOrNull(existing.providerId)
if (provider == null) {{
    return JsonOutput.toJson([success: false, error: "Provider not found: " + existing.providerId])
}}

def decoded = new String("{content_b64}".decodeBase64())

store.remove(existing.id)
def config = provider.newConfig(existing.id, "{name}", "{comment}", decoded)
store.save(config)
return JsonOutput.toJson([success: true, id: "{config_id}"])
'''
    result = jk.run_script(script)
    try:
        return json.loads(result)
    except:
        return {'success': True, 'id': config_id, 'raw': result}


async def delete_config_file(jk: Jenkins, config_id: str) -> dict:
    """删除文件配置"""
    script = f'''
import groovy.json.JsonOutput
import org.jenkinsci.plugins.configfiles.GlobalConfigFiles

def store = GlobalConfigFiles.get()
def existing = store.getById("{config_id}")
if (existing == null) {{
    return JsonOutput.toJson([success: false, error: "Config not found: {config_id}"])
}}

store.remove(existing.id)
return JsonOutput.toJson([success: true, id: "{config_id}"])
'''
    result = jk.run_script(script)
    try:
        return json.loads(result)
    except:
        return {'success': True, 'id': config_id, 'raw': result}


async def get_all_config_providers(jk: Jenkins) -> list:
    """获取所有可用的文件提供者类型"""
    script = '''
import groovy.json.JsonOutput
import org.jenkinsci.lib.configprovider.ConfigProvider

def result = ConfigProvider.all().collect { p ->
    [
        providerId: p.providerId,
        displayName: p.displayName
    ]
}
return JsonOutput.toJson(result)
'''
    result = jk.run_script(script)
    if result:
        try:
            return json.loads(result)
        except:
            return [{'error': 'Failed to parse result', 'raw': result}]
    return []


async def get_config_files_by_provider(jk: Jenkins, provider_id: str) -> list:
    """按提供者类型获取配置文件列表"""
    script = f'''
import groovy.json.JsonOutput
import org.jenkinsci.plugins.configfiles.GlobalConfigFiles
import org.jenkinsci.lib.configprovider.ConfigProvider

def provider = ConfigProvider.getByIdOrNull("{provider_id}")
if (provider == null) {{
    return JsonOutput.toJson([success: false, error: "Provider not found: {provider_id}"])
}}

def store = GlobalConfigFiles.get()
def configs = store.getConfigs(provider.getClass())
def result = configs.collect {{ c ->
    [
        id: c.id,
        name: c.name,
        comment: c.comment,
        providerId: c.providerId
    ]
}}
return JsonOutput.toJson(result)
'''
    result = jk.run_script(script)
    if result:
        try:
            return json.loads(result)
        except:
            return [{'error': 'Failed to parse result', 'raw': result}]
    return []
