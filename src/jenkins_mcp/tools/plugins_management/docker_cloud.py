"""
Docker Plugin (docker-plugin) 云管理模块

支持对Jenkins docker-plugin的云管理:
- 查看Docker云配置
- 创建/更新/删除Docker云
- 查看Docker模板
- 添加/更新/删除模板
- 复制模板
"""

import json
from typing import Optional

from jenkins_mcp.jenkins import Jenkins, JenkinsException


def _run_groovy(jk, script: str) -> str:
    return jk.run_script(script)


async def get_docker_clouds(jk: Jenkins) -> list:
    """获取所有Docker云配置列表"""
    script = '''
import com.nirima.jenkins.plugins.docker.DockerCloud
import jenkins.model.Jenkins
import groovy.json.JsonOutput

def result = []
Jenkins.getInstance().clouds.each { cloud ->
    if (cloud instanceof DockerCloud) {
        result << [
            name: cloud.name,
            dockerHost: cloud.dockerApi?.dockerHost?.dockerUri ?: '',
            containerCap: cloud.containerCap,
            disabled: cloud.disabled?.disabledByChoice ?: false,
            templateCount: cloud.templates?.size() ?: 0
        ]
    }
}
return JsonOutput.toJson(result)
'''
    try:
        result = _run_groovy(jk, script)
        return json.loads(result)
    except Exception as e:
        raise JenkinsException(f'Failed to get Docker clouds: {e}')


async def get_docker_cloud(jk: Jenkins, cloud_name: str) -> Optional[dict]:
    """获取指定Docker云配置详情"""
    script = f'''
import com.nirima.jenkins.plugins.docker.DockerCloud
import com.nirima.jenkins.plugins.docker.DockerTemplate
import io.jenkins.docker.client.DockerAPI
import jenkins.model.Jenkins
import groovy.json.JsonOutput

def cloud = Jenkins.getInstance().clouds.find {{ it.name == "{cloud_name}" && it instanceof DockerCloud }}
if (!cloud) return "null"

def gp = {{ obj, prop, defVal = null ->
    try {{ return obj != null && obj.hasProperty(prop) ? obj."$prop" : defVal }} catch (Exception e) {{ return defVal }}
}}

def templates = (cloud.templates ?: []).collect {{ t ->
    def tpl = [
        name: gp(t, 'name', ''),
        label: gp(t, 'labelString', ''),
        image: gp(t.dockerTemplateBase, 'image', ''),
        instanceCap: gp(t, 'instanceCap', 0),
        remoteFs: gp(t, 'remoteFs', ''),
        command: gp(t.dockerTemplateBase, 'dockerCommand', ''),
        hostname: gp(t.dockerTemplateBase, 'hostname', ''),
        user: gp(t.dockerTemplateBase, 'user', ''),
        memoryLimit: gp(t.dockerTemplateBase, 'memoryLimit', 0),
        memorySwap: gp(t.dockerTemplateBase, 'memorySwap', 0),
        cpuShares: gp(t.dockerTemplateBase, 'cpuShares', 0),
        cpus: gp(t.dockerTemplateBase, 'cpus', ''),
        cpuPeriod: gp(t.dockerTemplateBase, 'cpuPeriod', 0),
        cpuQuota: gp(t.dockerTemplateBase, 'cpuQuota', 0),
        shmSize: gp(t.dockerTemplateBase, 'shmSize', 0),
        privileged: gp(t.dockerTemplateBase, 'privileged', false),
        tty: gp(t.dockerTemplateBase, 'tty', false),
        network: gp(t.dockerTemplateBase, 'network', ''),
        macAddress: gp(t.dockerTemplateBase, 'macAddress', ''),
        dnsHosts: gp(t.dockerTemplateBase, 'dnsHosts', []),
        dnsSearch: gp(t.dockerTemplateBase, 'dnsSearch', []),
        mounts: gp(t.dockerTemplateBase, 'mounts', []),
        volumesFrom: gp(t.dockerTemplateBase, 'volumesFrom2', []),
        devices: gp(t.dockerTemplateBase, 'devices', []),
        environment: gp(t.dockerTemplateBase, 'environment', []),
        bindPorts: gp(t.dockerTemplateBase, 'bindPorts', ''),
        bindAllPorts: gp(t.dockerTemplateBase, 'bindAllPorts', false),
        extraHosts: gp(t.dockerTemplateBase, 'extraHosts', []),
        securityOpts: gp(t.dockerTemplateBase, 'securityOpts', []),
        capabilitiesToAdd: gp(t.dockerTemplateBase, 'capabilitiesToAdd', []),
        capabilitiesToDrop: gp(t.dockerTemplateBase, 'capabilitiesToDrop', []),
        extraGroups: gp(t.dockerTemplateBase, 'extraGroups', []),
        extraDockerLabels: gp(t.dockerTemplateBase, 'extraDockerLabels', [:]),
        pullCredentialsId: gp(t.dockerTemplateBase, 'pullCredentialsId', ''),
        removeVolumes: gp(t, 'removeVolumes', false),
        stopTimeout: gp(t, 'stopTimeout', 10),
        pullTimeout: gp(t, 'pullTimeout', 0),
        pullStrategy: gp(t, 'pullStrategy', '')?.toString() ?: '',
        connectorType: t.connector?.class?.simpleName ?: '',
        nodeUsageMode: gp(t, 'mode', '')?.toString() ?: '',
        disabled: gp(t, 'disabled', null)?.disabledByChoice ?: false
    ]
    return tpl
}}

def api = cloud.dockerApi
def result = [
    name: cloud.name,
    class: cloud.class.name,
    serverUrl: gp(api, 'dockerHost', null)?.dockerUri ?: '',
    credentialsId: gp(api, 'dockerHost', null)?.credentialsId ?: '',
    connectTimeout: gp(api, 'connectTimeout', 5),
    readTimeout: gp(api, 'readTimeout', 15),
    apiVersion: gp(api, 'apiVersion', ''),
    containerCap: cloud.containerCap,
    disabled: cloud.disabled?.disabledByChoice ?: false,
    errorDuration: cloud.errorDuration ?: 0,
    exposeDockerHost: cloud.exposeDockerHost ?: false,
    templates: templates
]
return JsonOutput.toJson(result)
'''
    try:
        result = _run_groovy(jk, script)
        return json.loads(result) if result else None
    except Exception as e:
        raise JenkinsException(f'Failed to get Docker cloud: {e}')


async def create_docker_cloud(
    jk: Jenkins,
    name: str,
    server_url: str,
    credentials_id: str = '',
    container_cap: int = 100,
    connect_timeout: int = 5,
    read_timeout: int = 15
) -> dict:
    """创建Docker云配置"""
    script = f'''
import com.nirima.jenkins.plugins.docker.DockerCloud
import io.jenkins.docker.client.DockerAPI
import io.jenkins.docker.client.DockerServerEndpoint
import jenkins.model.Jenkins

def existing = Jenkins.getInstance().clouds.find {{ it.name == "{name}" }}
if (existing) return "{{\\"error\\": \\"Docker cloud already exists: {name}\\"}}"

def endpoint = new DockerServerEndpoint("{server_url}", "{credentials_id}")
def api = new DockerAPI(endpoint, {connect_timeout}, {read_timeout}, null, null)
def cloud = new DockerCloud("{name}", api, [])
cloud.containerCap = {container_cap}

Jenkins.getInstance().clouds.add(cloud)
Jenkins.getInstance().save()
return "{{\\"success\\": true, \\"name\\": \\"{name}\\"}}"
'''
    try:
        result = _run_groovy(jk, script)
        return json.loads(result)
    except Exception as e:
        raise JenkinsException(f'Failed to create Docker cloud: {e}')


async def delete_docker_cloud(jk: Jenkins, cloud_name: str) -> dict:
    """删除Docker云配置"""
    script = f'''
import com.nirima.jenkins.plugins.docker.DockerCloud
import jenkins.model.Jenkins

def cloud = Jenkins.getInstance().clouds.find {{ it.name == "{cloud_name}" && it instanceof DockerCloud }}
if (!cloud) return "{{\\"error\\": \\"Docker cloud not found: {cloud_name}\\"}}"

Jenkins.getInstance().clouds.remove(cloud)
Jenkins.getInstance().save()
return "{{\\"success\\": true, \\"name\\": \\"{cloud_name}\\"}}"
'''
    try:
        result = _run_groovy(jk, script)
        return json.loads(result)
    except Exception as e:
        raise JenkinsException(f'Failed to delete Docker cloud: {e}')


async def get_docker_templates(jk: Jenkins, cloud_name: str) -> list:
    """获取Docker云的所有模板列表"""
    script = f'''
import com.nirima.jenkins.plugins.docker.DockerCloud
import jenkins.model.Jenkins
import groovy.json.JsonOutput

def cloud = Jenkins.getInstance().clouds.find {{ it.name == "{cloud_name}" && it instanceof DockerCloud }}
if (!cloud) return "[]"

def gp = {{ obj, prop, defVal = null ->
    try {{ return obj != null && obj.hasProperty(prop) ? obj."$prop" : defVal }} catch (Exception e) {{ return defVal }}
}}

def result = (cloud.templates ?: []).collect {{ t ->
    [
        name: gp(t, 'name', ''),
        label: gp(t, 'labelString', ''),
        image: gp(t.dockerTemplateBase, 'image', ''),
        instanceCap: gp(t, 'instanceCap', 0),
        remoteFs: gp(t, 'remoteFs', ''),
        connectorType: t.connector?.class?.simpleName ?: '',
        disabled: gp(t, 'disabled', null)?.disabledByChoice ?: false
    ]
}}
return JsonOutput.toJson(result)
'''
    try:
        result = _run_groovy(jk, script)
        return json.loads(result)
    except Exception as e:
        raise JenkinsException(f'Failed to get Docker templates: {e}')


async def get_docker_template(jk: Jenkins, cloud_name: str, template_name: str) -> Optional[dict]:
    """获取Docker云中指定模板详情"""
    script = f'''
import com.nirima.jenkins.plugins.docker.DockerCloud
import com.nirima.jenkins.plugins.docker.DockerTemplate
import com.nirima.jenkins.plugins.docker.DockerTemplateBase
import jenkins.model.Jenkins
import groovy.json.JsonOutput

def cloud = Jenkins.getInstance().clouds.find {{ it.name == "{cloud_name}" && it instanceof DockerCloud }}
if (!cloud) return "null"

def t = cloud.templates.find {{ it.name == "{template_name}" || it.dockerTemplateBase?.image == "{template_name}" }}
if (!t) return "null"

def gp = {{ obj, prop, defVal = null ->
    try {{ return obj != null && obj.hasProperty(prop) ? obj."$prop" : defVal }} catch (Exception e) {{ return defVal }}
}}

def result = [
    name: gp(t, 'name', ''),
    label: gp(t, 'labelString', ''),
    image: gp(t.dockerTemplateBase, 'image', ''),
    instanceCap: gp(t, 'instanceCap', 0),
    remoteFs: gp(t, 'remoteFs', ''),
    command: gp(t.dockerTemplateBase, 'dockerCommand', ''),
    hostname: gp(t.dockerTemplateBase, 'hostname', ''),
    user: gp(t.dockerTemplateBase, 'user', ''),
    memoryLimit: gp(t.dockerTemplateBase, 'memoryLimit', 0),
    memorySwap: gp(t.dockerTemplateBase, 'memorySwap', 0),
    cpuShares: gp(t.dockerTemplateBase, 'cpuShares', 0),
    cpus: gp(t.dockerTemplateBase, 'cpus', ''),
    cpuPeriod: gp(t.dockerTemplateBase, 'cpuPeriod', 0),
    cpuQuota: gp(t.dockerTemplateBase, 'cpuQuota', 0),
    shmSize: gp(t.dockerTemplateBase, 'shmSize', 0),
    privileged: gp(t.dockerTemplateBase, 'privileged', false),
    tty: gp(t.dockerTemplateBase, 'tty', false),
    network: gp(t.dockerTemplateBase, 'network', ''),
    macAddress: gp(t.dockerTemplateBase, 'macAddress', ''),
    dnsHosts: gp(t.dockerTemplateBase, 'dnsHosts', []),
    dnsSearch: gp(t.dockerTemplateBase, 'dnsSearch', []),
    mounts: gp(t.dockerTemplateBase, 'mounts', []),
    volumesFrom: gp(t.dockerTemplateBase, 'volumesFrom2', []),
    devices: gp(t.dockerTemplateBase, 'devices', []),
    environment: gp(t.dockerTemplateBase, 'environment', []),
    bindPorts: gp(t.dockerTemplateBase, 'bindPorts', ''),
    bindAllPorts: gp(t.dockerTemplateBase, 'bindAllPorts', false),
    extraHosts: gp(t.dockerTemplateBase, 'extraHosts', []),
    securityOpts: gp(t.dockerTemplateBase, 'securityOpts', []),
    capabilitiesToAdd: gp(t.dockerTemplateBase, 'capabilitiesToAdd', []),
    capabilitiesToDrop: gp(t.dockerTemplateBase, 'capabilitiesToDrop', []),
    extraGroups: gp(t.dockerTemplateBase, 'extraGroups', []),
    extraDockerLabels: gp(t.dockerTemplateBase, 'extraDockerLabels', [:]),
    pullCredentialsId: gp(t.dockerTemplateBase, 'pullCredentialsId', ''),
    removeVolumes: gp(t, 'removeVolumes', false),
    stopTimeout: gp(t, 'stopTimeout', 10),
    pullTimeout: gp(t, 'pullTimeout', 0),
    connectorType: t.connector?.class?.simpleName ?: '',
    nodeUsageMode: gp(t, 'mode', '')?.toString() ?: '',
    disabled: gp(t, 'disabled', null)?.disabledByChoice ?: false
]
return JsonOutput.toJson(result)
'''
    try:
        result = _run_groovy(jk, script)
        return json.loads(result) if result else None
    except Exception as e:
        raise JenkinsException(f'Failed to get Docker template: {e}')


async def add_docker_template(jk: Jenkins, cloud_name: str, template_config: dict) -> dict:
    """添加Docker模板到云

    参数:
        cloud_name: Docker云名称
        template_config: 模板配置 {
            name: str, image: str (必填),
            label: str, instanceCap: int, remoteFs: str,
            command: str, memoryLimit: int, cpus: str,
            privileged: bool, tty: bool, network: str,
            mounts: list, environment: list, bindPorts: str,
            extraHosts: list, dnsHosts: list, ...
        }
    """
    name = template_config.get('name', 'docker')
    image = template_config.get('image', '')
    label = template_config.get('label', '')
    instanceCap = template_config.get('instanceCap', 0)
    remoteFs = template_config.get('remoteFs', '/home/jenkins')
    command = template_config.get('command', '')
    memoryLimit = template_config.get('memoryLimit', 0) or 0
    cpus = template_config.get('cpus', '')
    privileged = 'true' if template_config.get('privileged') else 'false'
    tty = 'true' if template_config.get('tty') else 'false'
    network = template_config.get('network', '')
    mounts = template_config.get('mounts', [])
    environment = template_config.get('environment', [])
    bindPorts = template_config.get('bindPorts', '')

    lines = ['def base = new DockerTemplateBase("' + image + '")']
    if command:
        lines.append('base.dockerCommand = "' + command + '"')
    if memoryLimit:
        lines.append('base.memoryLimit = ' + str(memoryLimit))
    if cpus:
        lines.append('base.cpus = "' + cpus + '"')
    lines.append('base.privileged = ' + privileged)
    lines.append('base.tty = ' + tty)
    if network:
        lines.append('base.network = "' + network + '"')
    if mounts:
        lines.append('base.mounts = ' + json.dumps(mounts))
    if environment:
        lines.append('base.environment = ' + json.dumps(environment))
    if bindPorts:
        lines.append('base.bindPorts = "' + bindPorts + '"')

    base_config = '\n'.join(lines)

    script = f'''
import com.nirima.jenkins.plugins.docker.DockerCloud
import com.nirima.jenkins.plugins.docker.DockerTemplate
import com.nirima.jenkins.plugins.docker.DockerTemplateBase
import io.jenkins.docker.connector.DockerComputerAttachConnector
import jenkins.model.Jenkins

def cloud = Jenkins.getInstance().clouds.find {{ it.name == "{cloud_name}" && it instanceof DockerCloud }}
if (!cloud) return "{{\\"error\\": \\"Docker cloud not found: {cloud_name}\\"}}"

def existing = cloud.templates.find {{ it.name == "{name}" }}
if (existing) return "{{\\"error\\": \\"Template already exists: {name}\\"}}"

{base_config}

def connector = new DockerComputerAttachConnector()
def template = new DockerTemplate(base, connector, "{label}", str({instanceCap}))
template.name = "{name}"
template.remoteFs = "{remoteFs}"

cloud.templates.add(template)
Jenkins.getInstance().save()
return "{{\\"success\\": true, \\"name\\": \\"{name}\\"}}"
'''
    try:
        result = _run_groovy(jk, script)
        return json.loads(result)
    except Exception as e:
        raise JenkinsException(f'Failed to add Docker template: {e}')


async def update_docker_template(jk: Jenkins, cloud_name: str, template_name: str, template_config: dict) -> dict:
    """更新Docker模板"""
    updates = {}
    for key in ['name', 'label', 'instanceCap', 'remoteFs', 'command', 'memoryLimit', 'cpus',
                'privileged', 'tty', 'network', 'mounts', 'environment', 'bindPorts',
                'extraHosts', 'dnsHosts', 'pullCredentialsId', 'stopTimeout', 'pullTimeout',
                'hostname', 'user', 'shmSize', 'macAddress', 'removeVolumes']:
        if key in template_config:
            updates[key] = template_config[key]

    updates_json = json.dumps(updates)

    script = f'''
import com.nirima.jenkins.plugins.docker.DockerCloud
import com.nirima.jenkins.plugins.docker.DockerTemplate
import com.nirima.jenkins.plugins.docker.DockerTemplateBase
import jenkins.model.Jenkins

def cloud = Jenkins.getInstance().clouds.find {{ it.name == "{cloud_name}" && it instanceof DockerCloud }}
if (!cloud) return "{{\\"error\\": \\"Docker cloud not found: {cloud_name}\\"}}"

def t = cloud.templates.find {{ it.name == "{template_name}" }}
if (!t) return "{{\\"error\\": \\"Template not found: {template_name}\\"}}"

def updates = {updates_json}
def base = t.dockerTemplateBase

if (updates.containsKey("name")) t.name = updates.name
if (updates.containsKey("label")) t.labelString = updates.label
if (updates.containsKey("instanceCap")) t.instanceCap = updates.instanceCap as int
if (updates.containsKey("remoteFs")) t.remoteFs = updates.remoteFs
if (updates.containsKey("command")) base.dockerCommand = updates.command
if (updates.containsKey("memoryLimit")) base.memoryLimit = updates.memoryLimit as int
if (updates.containsKey("cpus")) base.cpus = updates.cpus
if (updates.containsKey("privileged")) base.privileged = updates.privileged as boolean
if (updates.containsKey("tty")) base.tty = updates.tty as boolean
if (updates.containsKey("network")) base.network = updates.network
if (updates.containsKey("mounts")) base.mounts = updates.mounts as String[]
if (updates.containsKey("environment")) base.environment = updates.environment as String[]
if (updates.containsKey("bindPorts")) base.bindPorts = updates.bindPorts
if (updates.containsKey("dnsHosts")) base.dnsHosts = updates.dnsHosts as String[]
if (updates.containsKey("extraHosts")) base.extraHosts = updates.extraHosts
if (updates.containsKey("pullCredentialsId")) base.pullCredentialsId = updates.pullCredentialsId
if (updates.containsKey("hostname")) base.hostname = updates.hostname
if (updates.containsKey("user")) base.user = updates.user
if (updates.containsKey("shmSize")) base.shmSize = updates.shmSize as int
if (updates.containsKey("macAddress")) base.macAddress = updates.macAddress
if (updates.containsKey("removeVolumes")) t.removeVolumes = updates.removeVolumes as boolean
if (updates.containsKey("stopTimeout")) t.stopTimeout = updates.stopTimeout as int
if (updates.containsKey("pullTimeout")) t.pullTimeout = updates.pullTimeout as int

Jenkins.getInstance().save()
return "{{\\"success\\": true, \\"name\\": \\"{template_name}\\"}}"
'''
    try:
        result = _run_groovy(jk, script)
        return json.loads(result)
    except Exception as e:
        raise JenkinsException(f'Failed to update Docker template: {e}')


async def delete_docker_template(jk: Jenkins, cloud_name: str, template_name: str) -> dict:
    """删除Docker云中的模板"""
    script = f'''
import com.nirima.jenkins.plugins.docker.DockerCloud
import jenkins.model.Jenkins

def cloud = Jenkins.getInstance().clouds.find {{ it.name == "{cloud_name}" && it instanceof DockerCloud }}
if (!cloud) return "{{\\"error\\": \\"Docker cloud not found: {cloud_name}\\"}}"

def t = cloud.templates.find {{ it.name == "{template_name}" }}
if (!t) return "{{\\"error\\": \\"Template not found: {template_name}\\"}}"

cloud.templates.remove(t)
Jenkins.getInstance().save()
return "{{\\"success\\": true, \\"name\\": \\"{template_name}\\"}}"
'''
    try:
        result = _run_groovy(jk, script)
        return json.loads(result)
    except Exception as e:
        raise JenkinsException(f'Failed to delete Docker template: {e}')


async def copy_docker_template(jk: Jenkins, cloud_name: str, source_template_name: str, new_template_name: str) -> dict:
    """复制Docker模板"""
    script = f'''
import com.nirima.jenkins.plugins.docker.DockerCloud
import com.nirima.jenkins.plugins.docker.DockerTemplate
import com.nirima.jenkins.plugins.docker.DockerTemplateBase
import jenkins.model.Jenkins

def cloud = Jenkins.getInstance().clouds.find {{ it.name == "{cloud_name}" && it instanceof DockerCloud }}
if (!cloud) return "{{\\"error\\": \\"Docker cloud not found: {cloud_name}\\"}}"

def source = cloud.templates.find {{ it.name == "{source_template_name}" }}
if (!source) return "{{\\"error\\": \\"Source template not found: {source_template_name}\\"}}"

def existing = cloud.templates.find {{ it.name == "{new_template_name}" }}
if (existing) return "{{\\"error\\": \\"Template already exists: {new_template_name}\\"}}"

// Copy DockerTemplateBase
def srcBase = source.dockerTemplateBase
def newBase = new DockerTemplateBase(srcBase.image)
newBase.dockerCommand = srcBase.dockerCommand
newBase.hostname = srcBase.hostname
newBase.user = srcBase.user
newBase.memoryLimit = srcBase.memoryLimit
newBase.memorySwap = srcBase.memorySwap
newBase.cpuShares = srcBase.cpuShares
newBase.cpus = srcBase.cpus
newBase.cpuPeriod = srcBase.cpuPeriod
newBase.cpuQuota = srcBase.cpuQuota
newBase.shmSize = srcBase.shmSize
newBase.privileged = srcBase.privileged
newBase.tty = srcBase.tty
newBase.network = srcBase.network
newBase.macAddress = srcBase.macAddress
newBase.bindPorts = srcBase.bindPorts
newBase.bindAllPorts = srcBase.bindAllPorts
newBase.dnsHosts = srcBase.dnsHosts
newBase.dnsSearch = srcBase.dnsSearch
newBase.mounts = srcBase.mounts
newBase.volumesFrom2 = srcBase.volumesFrom2
newBase.devices = srcBase.devices
newBase.environment = srcBase.environment
newBase.extraHosts = srcBase.extraHosts
newBase.securityOpts = srcBase.securityOpts
newBase.capabilitiesToAdd = srcBase.capabilitiesToAdd
newBase.capabilitiesToDrop = srcBase.capabilitiesToDrop
newBase.extraGroups = srcBase.extraGroups
newBase.extraDockerLabels = srcBase.extraDockerLabels
newBase.pullCredentialsId = srcBase.pullCredentialsId

// Create new template
def newTemplate = new DockerTemplate(newBase, source.connector, source.labelString, source.instanceCap as String)
newTemplate.name = "{new_template_name}"
newTemplate.remoteFs = source.remoteFs
newTemplate.removeVolumes = source.removeVolumes
newTemplate.stopTimeout = source.stopTimeout
newTemplate.pullTimeout = source.pullTimeout
newTemplate.nodeProperties = source.nodeProperties

cloud.templates.add(newTemplate)
Jenkins.getInstance().save()
return "{{\\"success\\": true, \\"name\\": \\"{new_template_name}\\"}}"
'''
    try:
        result = _run_groovy(jk, script)
        return json.loads(result)
    except Exception as e:
        raise JenkinsException(f'Failed to copy Docker template: {e}')



