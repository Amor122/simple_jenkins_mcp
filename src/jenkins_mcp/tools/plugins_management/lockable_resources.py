"""
Lockable Resources Plugin管理模块

支持对Jenkins lockable-resources-plugin的管理:
- 查看当前锁资源
- 添加锁资源
- 删除锁资源
"""

import json
from typing import Optional, List, Dict

import requests
from jenkins_mcp.jenkins import Jenkins, JenkinsException
from jenkins_mcp.tools.utils import verify_credentials, create_jenkins_client


async def get_all_lockable_resources(jk: Jenkins) -> list:
    """获取所有锁资源
    
    通过REST API获取lockable-resources-plugin的资源列表
    """
    try:
        response = jk.jenkins_open(
            requests.Request('GET', jk._build_url('lockable-resources/api/json'))
        )
        data = json.loads(response)
        return data.get('resources', [])
    except Exception:
        script = '''
import org.jenkins.plugins.lockableresources.LockableResourcesManager
import org.jenkins.plugins.lockableresources.LockableResource
def resources = LockableResourcesManager.get().getReadOnlyResources()
def result = resources.collect { r ->
    [
        name: r.name,
        labels: r.labels,
        description: r.description,
        locked: r.locked,
        reserved: r.reserved,
        reservedBy: r.reservedBy,
        queued: r.queued,
        note: r.note,
        ephemeral: r.ephemeral,
        lockReason: r.lockReason,
        queueItemProject: r.queueItemProject,
        properties: r.properties.collect {{ p -> [name: p.name, value: p.value] }}
    ]
}
return result
'''
        result = jk.run_script(script)
        if result:
            try:
                return json.loads(result)
            except:
                return [{'error': 'Failed to parse result', 'raw': result}]
        return []


async def get_lockable_resource(jk: Jenkins, name: str) -> Optional[dict]:
    """获取指定锁资源详情"""
    resources = await get_all_lockable_resources(jk)
    for r in resources:
        if r.get('name') == name:
            return r
    return None


async def add_lockable_resource(
    jk: Jenkins, 
    name: str, 
    labels: str = '', 
    description: str = '',
    allow_ephemeral: bool = True,
    properties: Dict[str, str] = None
) -> dict:
    return await _add_lockable_resource(jk, name, labels, description, allow_ephemeral, properties)


async def _add_lockable_resource(
    jk: Jenkins, 
    name: str, 
    labels: str = '', 
    description: str = '',
    allow_ephemeral: bool = True,
    properties: Dict[str, str] = None
) -> dict:
    labels = labels or ''
    description = description or ''
    props = properties if properties else {}
    props_json = json.dumps(props)
    
    script = f'''
import org.jenkins.plugins.lockableresources.LockableResourcesManager
import org.jenkins.plugins.lockableresources.LockableResource
import org.jenkins.plugins.lockableresources.LockableResourceProperty

def lrm = LockableResourcesManager.get()
def existing = lrm.fromName("{name}")
if (existing != null) {{
    return [success: false, error: "Resource already exists"]
}}

def resource = new org.jenkins.plugins.lockableresources.LockableResource("{name}")
resource.setEphemeral({str(allow_ephemeral).lower()})
'''
    
    if labels:
        script += f'''
resource.setLabels("{labels}")
'''
    
    if description:
        script += f'''
resource.setDescription("{description}")
'''
    
    if props:
        script += f'''
def propList = {props_json}.collect {{ k, v ->
    def p = new LockableResourceProperty()
    p.setName(k)
    p.setValue(v)
    return p
}}
resource.setProperties(propList)
'''
    
    script += f'''

def success = lrm.addResource(resource, true)
return [success: success, name: "{name}", properties: {props_json}]
'''
    
    result = jk.run_script(script)
    try:
        return json.loads(result)
    except:
        return {'success': True, 'name': name, 'raw': result}


async def add_lockable_resource_secure(
    username: str, api_token: str, name: str,
    labels: str = '', description: str = '',
    allow_ephemeral: bool = True,
    properties: dict = None, confirm: bool = False
) -> dict:
    """添加锁资源（需管理员权限）

    第一次调用时不传 confirm=True 会返回确认信息，
    确认无误后第二次调用时传入 confirm=True 执行。

    参数:
        username: 具有管理员权限的Jenkins用户名
        api_token: Jenkins API Token
        name: 资源名称
        labels: 可选，资源标签（多个用空格分隔）
        description: 可选，资源描述
        allow_ephemeral: 可选，是否允许临时资源（默认 True）
        properties: 可选，键值对属性
        confirm: 确认执行
    """
    cred_info = await verify_credentials(username, api_token)
    if cred_info["is_admin"] is False:
        raise PermissionError(
            f"用户 [{cred_info['user_id']}] 没有管理员权限，无法添加锁资源。\n"
            f"请使用具有管理员权限的 Jenkins 账户和 API Token。"
        )
    admin_status = "已验证 ✓" if cred_info["is_admin"] is True else "无法自动验证，将交由 Jenkins 鉴权"
    if not confirm:
        raise ValueError(
            f"⚠️  危险操作确认\n\n"
            f"操作: 添加锁资源\n"
            f"资源名称: {name}\n"
            f"标签: {labels or '(无)'}\n"
            f"当前用户: {cred_info['user_id']} ({cred_info['full_name']})\n"
            f"管理员身份: {admin_status}\n\n"
            f"如确认执行，请传入参数 confirm=True"
        )
    jk = create_jenkins_client(username, api_token)
    return await _add_lockable_resource(jk, name, labels, description, allow_ephemeral, properties=properties)


async def _delete_lockable_resource(jk: Jenkins, name: str) -> dict:
    script = f'''
import org.jenkins.plugins.lockableresources.LockableResourcesManager
import org.jenkins.plugins.lockableresources.LockableResource

def lrm = LockableResourcesManager.get()
def resource = lrm.fromName("{name}")
if (resource == null) {{
    return [success: false, error: "Resource not found"]
}}

if (resource.locked || resource.reserved) {{
    def resources = java.util.Collections.singletonList(resource)
    lrm.reset(resources)
    lrm.unreserve(resources)
}}

def resources = lrm.getResources()
def removed = resources.remove(resource)
lrm.save()
return [success: true, name: "{name}"]
'''
    result = jk.run_script(script)
    try:
        return json.loads(result)
    except:
        return {'success': True, 'name': name, 'raw': result}


async def delete_lockable_resource(jk: Jenkins, name: str) -> dict:
    return await _delete_lockable_resource(jk, name)


async def delete_lockable_resource_secure(username: str, api_token: str, name: str, confirm: bool = False) -> dict:
    """删除指定锁资源（需管理员权限）

    第一次调用时不传 confirm=True 会返回确认信息，
    确认无误后第二次调用时传入 confirm=True 执行。
    """
    cred_info = await verify_credentials(username, api_token)
    if cred_info["is_admin"] is False:
        raise PermissionError(
            f"用户 [{cred_info['user_id']}] 没有管理员权限，无法删除锁资源。\n"
            f"请使用具有管理员权限的 Jenkins 账户和 API Token。"
        )
    admin_status = "已验证 ✓" if cred_info["is_admin"] is True else "无法自动验证，将交由 Jenkins 鉴权"
    if not confirm:
        raise ValueError(
            f"⚠️  危险操作确认\n\n"
            f"操作: 删除锁资源\n"
            f"资源名称: {name}\n"
            f"当前用户: {cred_info['user_id']} ({cred_info['full_name']})\n"
            f"管理员身份: {admin_status}\n\n"
            f"如确认执行，请传入参数 confirm=True"
        )
    jk = create_jenkins_client(username, api_token)
    return await _delete_lockable_resource(jk, name)


async def _unlock_lockable_resource(jk: Jenkins, name: str) -> dict:
    script = f'''
import org.jenkins.plugins.lockableresources.LockableResourcesManager
def lrm = LockableResourcesManager.get()
def resource = lrm.fromName("{name}")
if (resource == null) {{
    return [success: false, error: "Resource not found"]
}}
def resources = java.util.Collections.singletonList(resource)
lrm.reset(resources)
return [success: true, name: "{name}"]
'''
    result = jk.run_script(script)
    try:
        return json.loads(result)
    except:
        return {'success': True, 'name': name}


async def unlock_lockable_resource(jk: Jenkins, name: str) -> dict:
    return await _unlock_lockable_resource(jk, name)


async def unlock_lockable_resource_secure(username: str, api_token: str, name: str, confirm: bool = False) -> dict:
    """解锁指定锁资源（需管理员权限）"""
    cred_info = await verify_credentials(username, api_token)
    if cred_info["is_admin"] is False:
        raise PermissionError(
            f"用户 [{cred_info['user_id']}] 没有管理员权限，无法解锁锁资源。\n"
            f"请使用具有管理员权限的 Jenkins 账户和 API Token。"
        )
    admin_status = "已验证 ✓" if cred_info["is_admin"] is True else "无法自动验证，将交由 Jenkins 鉴权"
    if not confirm:
        raise ValueError(
            f"⚠️  危险操作确认\n\n"
            f"操作: 解锁锁资源\n"
            f"资源名称: {name}\n"
            f"当前用户: {cred_info['user_id']} ({cred_info['full_name']})\n"
            f"管理员身份: {admin_status}\n\n"
            f"如确认执行，请传入参数 confirm=True"
        )
    jk = create_jenkins_client(username, api_token)
    return await _unlock_lockable_resource(jk, name)


async def reserve_lockable_resource(jk: Jenkins, name: str, user: str = 'admin', reason: str = '') -> dict:
    """预留指定锁资源"""
    reason = reason or ''
    script = f'''
import org.jenkins.plugins.lockableresources.LockableResourcesManager
def lrm = LockableResourcesManager.get()
def resource = lrm.fromName("{name}")
if (resource == null) {{
    return [success: false, error: "Resource not found"]
}}
def resources = java.util.Collections.singletonList(resource)
def success = lrm.reserve(resources, "{user}", "{reason}")
return [success: success, name: "{name}", user: "{user}"]
'''
    result = jk.run_script(script)
    try:
        return json.loads(result)
    except:
        return {'success': True, 'name': name, 'user': user}


async def unreserve_lockable_resource(jk: Jenkins, name: str) -> dict:
    """取消预留指定锁资源"""
    script = f'''
import org.jenkins.plugins.lockableresources.LockableResourcesManager
def lrm = LockableResourcesManager.get()
def resource = lrm.fromName("{name}")
if (resource == null) {{
    return [success: false, error: "Resource not found"]
}}
def resources = java.util.Collections.singletonList(resource)
lrm.unreserve(resources)
return [success: true, name: "{name}"]
'''
    result = jk.run_script(script)
    try:
        return json.loads(result)
    except:
        return {'success': True, 'name': name}


async def get_lockable_queue(jk: Jenkins) -> list:
    """获取锁资源队列信息"""
    script = '''
import org.jenkins.plugins.lockableresources.LockableResourcesManager

def lrm = LockableResourcesManager.get()
def queue = lrm.getCurrentQueuedContext()

def result = queue.collect { ctx ->
    [
        id: ctx.id,
        priority: ctx.priority,
        resources: ctx.resources.collect { r ->
            [name: r.label, requiredNumber: r.requiredNumber]
        },
        build: ctx.build?.fullDisplayName,
        timestamp: ctx.queuedAt
    ]
}
return result
'''
    
    result = jk.run_script(script)
    try:
        return json.loads(result)
    except:
        return []


async def lockable_resource_exists(jk: Jenkins, name: str) -> bool:
    """检查锁资源是否存在"""
    resource = await get_lockable_resource(jk, name)
    return resource is not None


async def _set_lockable_resource_properties(jk: Jenkins, name: str, properties: dict) -> dict:
    props_json = json.dumps(properties)
    script = f'''
import org.jenkins.plugins.lockableresources.LockableResourcesManager
import org.jenkins.plugins.lockableresources.LockableResourceProperty

def lrm = LockableResourcesManager.get()
def resource = lrm.fromName("{name}")
if (resource == null) {{
    return [success: false, error: "Resource not found"]
}}

def props = {props_json}.collect {{ k, v ->
    def p = new LockableResourceProperty()
    p.setName(k)
    p.setValue(v)
    return p
}}
resource.setProperties(props)
lrm.save()
return [success: true, name: "{name}", properties: {props_json}]
'''
    result = jk.run_script(script)
    try:
        return json.loads(result)
    except:
        return {'success': True, 'name': name, 'properties': properties}


async def set_lockable_resource_properties(jk: Jenkins, name: str, properties: dict) -> dict:
    return await _set_lockable_resource_properties(jk, name, properties)


async def set_lockable_resource_properties_secure(
    username: str, api_token: str, name: str, properties: dict, confirm: bool = False
) -> dict:
    """设置锁资源的属性（替换所有属性，需管理员权限）"""
    cred_info = await verify_credentials(username, api_token)
    if cred_info["is_admin"] is False:
        raise PermissionError(
            f"用户 [{cred_info['user_id']}] 没有管理员权限，无法设置锁资源属性。\n"
            f"请使用具有管理员权限的 Jenkins 账户和 API Token。"
        )
    admin_status = "已验证 ✓" if cred_info["is_admin"] is True else "无法自动验证，将交由 Jenkins 鉴权"
    if not confirm:
        raise ValueError(
            f"⚠️  危险操作确认\n\n"
            f"操作: 设置锁资源属性\n"
            f"资源名称: {name}\n"
            f"当前用户: {cred_info['user_id']} ({cred_info['full_name']})\n"
            f"管理员身份: {admin_status}\n\n"
            f"如确认执行，请传入参数 confirm=True"
        )
    jk = create_jenkins_client(username, api_token)
    return await _set_lockable_resource_properties(jk, name, properties)


async def _set_lockable_resource_property(jk: Jenkins, name: str, key: str, value: str) -> dict:
    script = f'''
import org.jenkins.plugins.lockableresources.LockableResourcesManager
import org.jenkins.plugins.lockableresources.LockableResourceProperty

def lrm = LockableResourcesManager.get()
def resource = lrm.fromName("{name}")
if (resource == null) {{
    return [success: false, error: "Resource not found"]
}}

def props = resource.getProperties()
def existingProp = props.find {{ it.name == "{key}" }}
if (existingProp != null) {{
    existingProp.setValue("{value}")
}} else {{
    def p = new LockableResourceProperty()
    p.setName("{key}")
    p.setValue("{value}")
    props.add(p)
}}
lrm.save()
return [success: true, name: "{name}", key: "{key}", value: "{value}"]
'''
    result = jk.run_script(script)
    try:
        return json.loads(result)
    except:
        return {'success': True, 'name': name, 'key': key, 'value': value}


async def set_lockable_resource_property(jk: Jenkins, name: str, key: str, value: str) -> dict:
    return await _set_lockable_resource_property(jk, name, key, value)


async def set_lockable_resource_property_secure(
    username: str, api_token: str, name: str, key: str, value: str, confirm: bool = False
) -> dict:
    """设置锁资源的单个属性（需管理员权限）"""
    cred_info = await verify_credentials(username, api_token)
    if cred_info["is_admin"] is False:
        raise PermissionError(
            f"用户 [{cred_info['user_id']}] 没有管理员权限，无法设置锁资源属性。\n"
            f"请使用具有管理员权限的 Jenkins 账户和 API Token。"
        )
    admin_status = "已验证 ✓" if cred_info["is_admin"] is True else "无法自动验证，将交由 Jenkins 鉴权"
    if not confirm:
        raise ValueError(
            f"⚠️  危险操作确认\n\n"
            f"操作: 设置锁资源属性\n"
            f"资源名称: {name}\n"
            f"属性: {key} = {value}\n"
            f"当前用户: {cred_info['user_id']} ({cred_info['full_name']})\n"
            f"管理员身份: {admin_status}\n\n"
            f"如确认执行，请传入参数 confirm=True"
        )
    jk = create_jenkins_client(username, api_token)
    return await _set_lockable_resource_property(jk, name, key, value)


async def get_lockable_resource_property(jk: Jenkins, name: str, key: str) -> Optional[str]:
    """获取锁资源的单个属性值
    
    参数:
        name: 资源名称
        key: 属性键
    
    返回:
        属性值，如果不存在返回None
    """
    resource = await get_lockable_resource(jk, name)
    if not resource:
        return None
    
    props = resource.get('properties', [])
    for p in props:
        if p.get('name') == key:
            return p.get('value')
    return None


async def get_all_lockable_labels(jk: Jenkins) -> list:
    """获取所有锁资源标签"""
    script = '''
import org.jenkins.plugins.lockableresources.LockableResourcesManager

def lrm = LockableResourcesManager.get()
def labels = lrm.getAllLabels()
return labels as groovy.json.JsonOutput.toJson(labels)
'''
    
    result = jk.run_script(script)
    try:
        return json.loads(result)
    except:
        return []


async def get_lockable_resources_by_label(jk: Jenkins, label: str) -> list:
    """获取具有指定标签的所有锁资源"""
    script = f'''
import org.jenkins.plugins.lockableresources.LockableResourcesManager

def lrm = LockableResourcesManager.get()
def resources = lrm.getResourcesWithLabel("{label}")

def result = resources.collect {{ r ->
    [
        name: r.name,
        labels: r.labels,
        description: r.description,
        locked: r.locked,
        reserved: r.reserved,
        reservedBy: r.reservedBy
    ]
}}
return result
'''
    
    result = jk.run_script(script)
    try:
        return json.loads(result)
    except:
        return []