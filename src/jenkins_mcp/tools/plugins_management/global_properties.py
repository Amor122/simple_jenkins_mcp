"""
Jenkins Global Properties 管理模块

管理 Jenkins 全局环境变量（Manage Jenkins → Configure System → Global Properties）
"""

import json
from jenkins_mcp.jenkins import Jenkins, JenkinsException
from jenkins_mcp.tools.utils import verify_credentials, create_jenkins_client


def _run_groovy(jk, script: str) -> str:
    return jk.run_script(script)


async def get_global_properties(jk: Jenkins) -> list:
    """获取所有全局环境变量"""
    script = '''
import jenkins.model.Jenkins
import hudson.slaves.EnvironmentVariablesNodeProperty
import groovy.json.JsonOutput

def nodeProps = Jenkins.getInstance().getGlobalNodeProperties()
def envProp = nodeProps.get(EnvironmentVariablesNodeProperty.class)
def result = []
if (envProp) {
    envProp.getEnvVars().each { k, v ->
        result.add([key: k, value: v])
    }
}
return JsonOutput.toJson(result)
'''
    try:
        result = _run_groovy(jk, script)
        return json.loads(result)
    except Exception as e:
        raise JenkinsException(f'Failed to get global properties: {e}')


async def set_global_property(username: str, api_token: str, key: str, value: str, confirm: bool = False) -> dict:
    """设置全局环境变量（新增或更新）

    需要提供具有管理员权限的Jenkins账户和API Token。
    第一次调用时不传 confirm=True 会返回确认信息，
    确认无误后第二次调用时传入 confirm=True 执行。
    """
    cred_info = await verify_credentials(username, api_token)
    if cred_info["is_admin"] is False:
        raise PermissionError(
            f"用户 [{cred_info['user_id']}] 没有管理员权限，无法设置全局环境变量。\n"
            f"请使用具有管理员权限的 Jenkins 账户和 API Token。"
        )
    admin_status = "已验证 ✓" if cred_info["is_admin"] is True else "无法自动验证，将交由 Jenkins 鉴权"
    if not confirm:
        raise ValueError(
            f"⚠️  危险操作确认\n\n"
            f"操作: 设置全局环境变量\n"
            f"变量: {key} = {value}\n"
            f"当前用户: {cred_info['user_id']} ({cred_info['full_name']})\n"
            f"管理员身份: {admin_status}\n\n"
            f"如确认执行，请传入参数 confirm=True"
        )
    jk = create_jenkins_client(username, api_token)
    import json as _json
    script = f'''
import jenkins.model.Jenkins
import hudson.slaves.EnvironmentVariablesNodeProperty
import groovy.json.JsonOutput

def nodeProps = Jenkins.getInstance().getGlobalNodeProperties()
def envProp = nodeProps.get(EnvironmentVariablesNodeProperty.class)
if (!envProp) {{
    envProp = new EnvironmentVariablesNodeProperty()
    Jenkins.getInstance().getGlobalNodeProperties().add(envProp)
}}
envProp.getEnvVars().put("{key}", "{value}")
Jenkins.getInstance().save()
return JsonOutput.toJson([success: true, key: "{key}", value: "{value}"])
'''
    try:
        result = _run_groovy(jk, script)
        return json.loads(result)
    except Exception as e:
        raise JenkinsException(f'Failed to set global property [{key}]: {e}')


async def delete_global_property(username: str, api_token: str, key: str, confirm: bool = False) -> dict:
    """删除全局环境变量

    需要提供具有管理员权限的Jenkins账户和API Token。
    第一次调用时不传 confirm=True 会返回确认信息，
    确认无误后第二次调用时传入 confirm=True 执行。
    """
    cred_info = await verify_credentials(username, api_token)
    if cred_info["is_admin"] is False:
        raise PermissionError(
            f"用户 [{cred_info['user_id']}] 没有管理员权限，无法删除全局环境变量。\n"
            f"请使用具有管理员权限的 Jenkins 账户和 API Token。"
        )
    admin_status = "已验证 ✓" if cred_info["is_admin"] is True else "无法自动验证，将交由 Jenkins 鉴权"
    if not confirm:
        raise ValueError(
            f"⚠️  危险操作确认\n\n"
            f"操作: 删除全局环境变量\n"
            f"变量: {key}\n"
            f"当前用户: {cred_info['user_id']} ({cred_info['full_name']})\n"
            f"管理员身份: {admin_status}\n\n"
            f"如确认执行，请传入参数 confirm=True"
        )
    jk = create_jenkins_client(username, api_token)
    import json as _json
    script = f'''
import jenkins.model.Jenkins
import hudson.slaves.EnvironmentVariablesNodeProperty
import groovy.json.JsonOutput

def nodeProps = Jenkins.getInstance().getGlobalNodeProperties()
def envProp = nodeProps.get(EnvironmentVariablesNodeProperty.class)
if (envProp) {{
    envProp.getEnvVars().remove("{key}")
    Jenkins.getInstance().save()
}}
return JsonOutput.toJson([success: true, key: "{key}"])
'''
    try:
        result = _run_groovy(jk, script)
        return json.loads(result)
    except Exception as e:
        raise JenkinsException(f'Failed to delete global property [{key}]: {e}')
