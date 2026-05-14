"""
Yet Another Docker Plugin (yad) 云管理模块

支持对Jenkins yet-another-docker-plugin的云管理:
- 查看YAD云配置
- 创建/更新/删除YAD云
- 查看Docker模板
- 添加/更新/删除模板
- 复制模板
"""

import json
from typing import Optional

from jenkins_mcp.jenkins import Jenkins, JenkinsException


def _run_groovy(jk, script: str) -> str:
    return jk.run_script(script)


async def get_yad_clouds(jk: Jenkins) -> list:
    """获取所有YAD云配置列表"""
    script = '''
import com.github.kostyasha.yad.DockerCloud
import jenkins.model.Jenkins
import groovy.json.JsonOutput

def result = []
Jenkins.getInstance().clouds.each { cloud ->
    if (cloud instanceof DockerCloud) {
        result << [
            name: cloud.name,
            serverUrl: cloud.connector?.serverUrl ?: '',
            containerCap: cloud.containerCap,
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
        raise JenkinsException(f'Failed to get YAD clouds: {e}')


async def get_yad_cloud(jk: Jenkins, cloud_name: str) -> Optional[dict]:
    """获取指定YAD云配置详情"""
    script = f'''
import com.github.kostyasha.yad.DockerCloud
import com.github.kostyasha.yad.DockerSlaveTemplate
import com.github.kostyasha.yad.DockerContainerLifecycle
import com.github.kostyasha.yad.DockerConnector
import com.github.kostyasha.yad.commons.DockerCreateContainer
import jenkins.model.Jenkins
import groovy.json.JsonOutput

def cloud = Jenkins.getInstance().clouds.find {{ it.name == "{cloud_name}" && it instanceof DockerCloud }}
if (!cloud) return "null"

def gp = {{ obj, prop, defVal = null ->
    try {{ return obj != null && obj.hasProperty(prop) ? obj."$prop" : defVal }} catch (Exception e) {{ return defVal }}
}}

def templates = (cloud.templates ?: []).collect {{ t ->
    def lifecycle = t.dockerContainerLifecycle
    def createContainer = lifecycle?.createContainer

    def result = [
        id: gp(t, 'id', ''),
        label: gp(t, 'labelString', ''),
        remoteFs: gp(t, 'remoteFs', '/home/jenkins'),
        numExecutors: gp(t, 'numExecutors', 1),
        maxCapacity: gp(t, 'maxCapacity', 10),
        mode: gp(t, 'mode', '')?.toString() ?: '',
        launcherClass: gp(t, 'launcher', null)?.class?.simpleName ?: '',
        // container lifecycle
        image: gp(lifecycle, 'image', ''),
        // create container fields
        command: gp(createContainer, 'command', ''),
        commands: gp(createContainer, 'commands', []),
        entrypoint: gp(createContainer, 'entrypoint', ''),
        hostname: gp(createContainer, 'hostname', ''),
        user: gp(createContainer, 'user', ''),
        workingDir: gp(createContainer, 'workdir', ''),
        memoryLimit: gp(createContainer, 'memoryLimit', 0),
        cpuShares: gp(createContainer, 'cpuShares', 0),
        privileged: gp(createContainer, 'privileged', false),
        tty: gp(createContainer, 'tty', false),
        networkMode: gp(createContainer, 'networkMode', ''),
        volumes: gp(createContainer, 'volumes', []),
        volumesFrom: gp(createContainer, 'volumesFrom', []),
        environment: gp(createContainer, 'environment', []),
        bindPorts: gp(createContainer, 'bindPorts', ''),
        bindAllPorts: gp(createContainer, 'bindAllPorts', false),
        dnsHosts: gp(createContainer, 'dnsHosts', []),
        extraHosts: gp(createContainer, 'extraHosts', []),
        devices: gp(createContainer, 'devices', []),
        shmSize: gp(createContainer, 'shmSize', 0),
        macAddress: gp(createContainer, 'macAddress', ''),
        restartPolicy: gp(createContainer, 'restartPolicy', null)?.toString() ?: '',
        links: gp(createContainer, 'links', []),
        subContainerCount: 0
    ]
    return result
}}

def api = cloud.connector
def result = [
    name: cloud.name,
    class: cloud.class.name,
    serverUrl: gp(api, 'serverUrl', ''),
    credentialsId: gp(api, 'credentialsId', ''),
    apiVersion: gp(api, 'apiVersion', ''),
    connectTimeout: gp(api, 'connectTimeout', 0),
    readTimeout: gp(api, 'readTimeout', 0),
    connectorType: gp(api, 'connectorType', '')?.toString() ?: '',
    containerCap: cloud.containerCap,
    templates: templates
]
return JsonOutput.toJson(result)
'''
    try:
        result = _run_groovy(jk, script)
        return json.loads(result) if result else None
    except Exception as e:
        raise JenkinsException(f'Failed to get YAD cloud: {e}')


async def create_yad_cloud(
    jk: Jenkins,
    name: str,
    server_url: str,
    credentials_id: str = '',
    container_cap: int = 50,
    connect_timeout: int = 0,
    read_timeout: int = 0
) -> dict:
    """创建YAD云配置"""
    lines = []
    lines.append('def connector = new DockerConnector("' + server_url + '")')
    if credentials_id:
        lines.append('connector.credentialsId = "' + credentials_id + '"')
    lines.append('connector.connectTimeout = ' + str(connect_timeout))
    lines.append('connector.readTimeout = ' + str(read_timeout))
    lines.append('')
    lines.append('def cloud = new DockerCloud("' + name + '", [], ' + str(container_cap) + ', connector)')
    lines.append('')
    lines.append('Jenkins.getInstance().clouds.add(cloud)')
    lines.append('Jenkins.getInstance().save()')
    lines.append('return "{\\"success\\": true, \\"name\\": \\"' + name + '\\"}"')

    script = '''import com.github.kostyasha.yad.DockerCloud
import com.github.kostyasha.yad.DockerConnector
import jenkins.model.Jenkins

def existing = Jenkins.getInstance().clouds.find { it.name == "''' + name + '''" && it instanceof DockerCloud }
if (existing) return "{\\"error\\": \\"YAD cloud already exists: ''' + name + '''\\"}"

'''
    script += '\n'.join(lines)
    try:
        result = _run_groovy(jk, script)
        return json.loads(result)
    except Exception as e:
        raise JenkinsException(f'Failed to create YAD cloud: {e}')


async def delete_yad_cloud(jk: Jenkins, cloud_name: str) -> dict:
    """删除YAD云配置"""
    script = f'''
import com.github.kostyasha.yad.DockerCloud
import jenkins.model.Jenkins

def cloud = Jenkins.getInstance().clouds.find {{ it.name == "{cloud_name}" && it instanceof DockerCloud }}
if (!cloud) return "{{\\"error\\": \\"YAD cloud not found: {cloud_name}\\"}}"

Jenkins.getInstance().clouds.remove(cloud)
Jenkins.getInstance().save()
return "{{\\"success\\": true, \\"name\\": \\"{cloud_name}\\"}}"
'''
    try:
        result = _run_groovy(jk, script)
        return json.loads(result)
    except Exception as e:
        raise JenkinsException(f'Failed to delete YAD cloud: {e}')


async def get_yad_templates(jk: Jenkins, cloud_name: str) -> list:
    """获取YAD云的所有模板列表"""
    script = f'''
import com.github.kostyasha.yad.DockerCloud
import com.github.kostyasha.yad.DockerSlaveTemplate
import jenkins.model.Jenkins
import groovy.json.JsonOutput

def cloud = Jenkins.getInstance().clouds.find {{ it.name == "{cloud_name}" && it instanceof DockerCloud }}
if (!cloud) return "[]"

def gp = {{ obj, prop, defVal = null ->
    try {{ return obj != null && obj.hasProperty(prop) ? obj."$prop" : defVal }} catch (Exception e) {{ return defVal }}
}}

def result = (cloud.templates ?: []).collect {{ t ->
    [
        id: gp(t, 'id', ''),
        label: gp(t, 'labelString', ''),
        image: gp(t.dockerContainerLifecycle, 'image', ''),
        remoteFs: gp(t, 'remoteFs', '/home/jenkins'),
        numExecutors: gp(t, 'numExecutors', 1),
        maxCapacity: gp(t, 'maxCapacity', 10),
        launcherClass: gp(t, 'launcher', null)?.class?.simpleName ?: ''
    ]
}}
return JsonOutput.toJson(result)
'''
    try:
        result = _run_groovy(jk, script)
        return json.loads(result)
    except Exception as e:
        raise JenkinsException(f'Failed to get YAD templates: {e}')


async def get_yad_template(jk: Jenkins, cloud_name: str, template_id: str) -> Optional[dict]:
    """获取YAD云中指定模板详情"""
    script = f'''
import com.github.kostyasha.yad.DockerCloud
import com.github.kostyasha.yad.DockerSlaveTemplate
import com.github.kostyasha.yad.DockerContainerLifecycle
import com.github.kostyasha.yad.commons.DockerCreateContainer
import jenkins.model.Jenkins
import groovy.json.JsonOutput

def cloud = Jenkins.getInstance().clouds.find {{ it.name == "{cloud_name}" && it instanceof DockerCloud }}
if (!cloud) return "null"

def t = cloud.templates.find {{ it.id == "{template_id}" || it.labelString == "{template_id}" }}
if (!t) return "null"

def gp = {{ obj, prop, defVal = null ->
    try {{ return obj != null && obj.hasProperty(prop) ? obj."$prop" : defVal }} catch (Exception e) {{ return defVal }}
}}

def lifecycle = t.dockerContainerLifecycle
def cc = lifecycle?.createContainer

def result = [
    id: gp(t, 'id', ''),
    label: gp(t, 'labelString', ''),
    remoteFs: gp(t, 'remoteFs', '/home/jenkins'),
    numExecutors: gp(t, 'numExecutors', 1),
    maxCapacity: gp(t, 'maxCapacity', 10),
    mode: gp(t, 'mode', '')?.toString() ?: '',
    launcherClass: gp(t, 'launcher', null)?.class?.simpleName ?: '',
    // Container lifecycle
    image: gp(lifecycle, 'image', ''),
    // DockerCreateContainer fields
    command: gp(cc, 'command', ''),
    commands: gp(cc, 'commands', []),
    entrypoint: gp(cc, 'entrypoint', ''),
    hostname: gp(cc, 'hostname', ''),
    user: gp(cc, 'user', ''),
    workingDir: gp(cc, 'workdir', ''),
    memoryLimit: gp(cc, 'memoryLimit', 0),
    cpuShares: gp(cc, 'cpuShares', 0),
    cpusetCpus: gp(cc, 'cpusetCpus', ''),
    cpusetMems: gp(cc, 'cpusetMems', ''),
    privileged: gp(cc, 'privileged', false),
    tty: gp(cc, 'tty', false),
    networkMode: gp(cc, 'networkMode', ''),
    volumes: gp(cc, 'volumes', []),
    volumesFrom: gp(cc, 'volumesFrom', []),
    environment: gp(cc, 'environment', []),
    bindPorts: gp(cc, 'bindPorts', ''),
    bindAllPorts: gp(cc, 'bindAllPorts', false),
    dnsHosts: gp(cc, 'dnsHosts', []),
    extraHosts: gp(cc, 'extraHosts', []),
    devices: gp(cc, 'devices', []),
    shmSize: gp(cc, 'shmSize', 0),
    macAddress: gp(cc, 'macAddress', ''),
    links: gp(cc, 'links', []),
    dockerLabels: gp(cc, 'dockerLabels', []),
    restartPolicyName: gp(cc, 'restartPolicy', null)?.name?.toString() ?: '',
    // Retention
    retentionStrategyClass: gp(t, 'retentionStrategy', null)?.class?.simpleName ?: ''
]
return JsonOutput.toJson(result)
'''
    try:
        result = _run_groovy(jk, script)
        return json.loads(result) if result else None
    except Exception as e:
        raise JenkinsException(f'Failed to get YAD template: {e}')


async def add_yad_template(jk: Jenkins, cloud_name: str, template_config: dict) -> dict:
    """添加YAD模板到云

    参数:
        cloud_name: YAD云名称
        template_config: 模板配置 {
            image: str (必填), label: str, remoteFs: str,
            numExecutors: int, maxCapacity: int,
            command: str, hostname: str, user: str,
            memoryLimit: int, cpuShares: int,
            privileged: bool, tty: bool, networkMode: str,
            volumes: list, environment: list, bindPorts: str,
            extraHosts: list, dnsHosts: list
        }
    """
    import json as _json

    name = template_config.get('image', '')
    label = template_config.get('label', 'docker')
    remoteFs = template_config.get('remoteFs', '/home/jenkins')
    numExecutors = template_config.get('numExecutors', 1)
    maxCapacity = template_config.get('maxCapacity', 10)
    command = template_config.get('command', '')
    hostname = template_config.get('hostname', '')
    user = template_config.get('user', '')
    memoryLimit = template_config.get('memoryLimit', 0) or 0
    cpuShares = template_config.get('cpuShares', 0) or 0
    privileged = 'true' if template_config.get('privileged') else 'false'
    tty = 'true' if template_config.get('tty') else 'false'
    networkMode = template_config.get('networkMode', '')
    volumes = template_config.get('volumes', [])
    environment = template_config.get('environment', [])
    bindPorts = template_config.get('bindPorts', '')
    extraHosts = template_config.get('extraHosts', [])
    dnsHosts = template_config.get('dnsHosts', [])

    lines = []
    lines.append('def lifecycle = new com.github.kostyasha.yad.DockerContainerLifecycle()')
    lines.append('lifecycle.image = "' + name + '"')
    if command:
        lines.append('lifecycle.createContainer.command = "' + command + '"')
    if hostname:
        lines.append('lifecycle.createContainer.hostname = "' + hostname + '"')
    if user:
        lines.append('lifecycle.createContainer.user = "' + user + '"')
    if memoryLimit:
        lines.append('lifecycle.createContainer.memoryLimit = ' + str(memoryLimit) + 'L')
    if cpuShares:
        lines.append('lifecycle.createContainer.cpuShares = ' + str(cpuShares))
    lines.append('lifecycle.createContainer.privileged = ' + privileged)
    lines.append('lifecycle.createContainer.tty = ' + tty)
    if networkMode:
        lines.append('lifecycle.createContainer.networkMode = "' + networkMode + '"')
    if volumes:
        lines.append('lifecycle.createContainer.volumes = ' + _json.dumps(volumes))
    if environment:
        lines.append('lifecycle.createContainer.environment = ' + _json.dumps(environment))
    if bindPorts:
        lines.append('lifecycle.createContainer.bindPorts = "' + bindPorts + '"')
    if extraHosts:
        lines.append('lifecycle.createContainer.extraHosts = ' + _json.dumps(extraHosts))
    if dnsHosts:
        lines.append('lifecycle.createContainer.dnsHosts = ' + _json.dumps(dnsHosts))

    lifecycle_config = '\n'.join(lines)

    script = f'''
import com.github.kostyasha.yad.DockerCloud
import com.github.kostyasha.yad.DockerSlaveTemplate
import com.github.kostyasha.yad.DockerContainerLifecycle
import com.github.kostyasha.yad.commons.DockerCreateContainer
import com.github.kostyasha.yad.launcher.DockerComputerJNLPLauncher
import com.github.kostyasha.yad.strategy.DockerOnceRetentionStrategy
import jenkins.model.Jenkins

def cloud = Jenkins.getInstance().clouds.find {{ it.name == "{cloud_name}" && it instanceof DockerCloud }}
if (!cloud) return "{{\\"error\\": \\"YAD cloud not found: {cloud_name}\\"}}"

def uuid = UUID.randomUUID().toString()
def existing = cloud.templates.find {{ it.labelString == "{label}" }}
if (existing) return "{{\\"error\\": \\"Template with label '{label}' already exists\\"}}"

{lifecycle_config}

def template = new DockerSlaveTemplate(uuid)
template.labelString = "{label}"
template.remoteFs = "{remoteFs}"
template.numExecutors = {numExecutors}
template.maxCapacity = {maxCapacity}
template.dockerContainerLifecycle = lifecycle
template.launcher = new DockerComputerJNLPLauncher()
template.retentionStrategy = new DockerOnceRetentionStrategy(10)

cloud.templates.add(template)
Jenkins.getInstance().save()
return "{{\\"success\\": true, \\"id\\": \\"" + uuid + "\\", \\"label\\": \\"{label}\\"}}"
'''
    try:
        result = _run_groovy(jk, script)
        return json.loads(result)
    except Exception as e:
        raise JenkinsException(f'Failed to add YAD template: {e}')


async def delete_yad_template(jk: Jenkins, cloud_name: str, template_id: str) -> dict:
    """删除YAD云中的模板"""
    script = f'''
import com.github.kostyasha.yad.DockerCloud
import jenkins.model.Jenkins

def cloud = Jenkins.getInstance().clouds.find {{ it.name == "{cloud_name}" && it instanceof DockerCloud }}
if (!cloud) return "{{\\"error\\": \\"YAD cloud not found: {cloud_name}\\"}}"

def t = cloud.templates.find {{ it.id == "{template_id}" || it.labelString == "{template_id}" }}
if (!t) return "{{\\"error\\": \\"Template not found: {template_id}\\"}}"

cloud.templates.remove(t)
Jenkins.getInstance().save()
return "{{\\"success\\": true, \\"id\\": \\"{template_id}\\"}}"
'''
    try:
        result = _run_groovy(jk, script)
        return json.loads(result)
    except Exception as e:
        raise JenkinsException(f'Failed to delete YAD template: {e}')


async def copy_yad_template(jk: Jenkins, cloud_name: str, source_template_id: str, new_label: str) -> dict:
    """复制YAD模板"""
    script = f'''
import com.github.kostyasha.yad.DockerCloud
import com.github.kostyasha.yad.DockerSlaveTemplate
import com.github.kostyasha.yad.DockerContainerLifecycle
import com.github.kostyasha.yad.commons.DockerCreateContainer
import com.github.kostyasha.yad.commons.DockerPullImage
import com.github.kostyasha.yad.commons.DockerStopContainer
import com.github.kostyasha.yad.commons.DockerRemoveContainer
import jenkins.model.Jenkins

def cloud = Jenkins.getInstance().clouds.find {{ it.name == "{cloud_name}" && it instanceof DockerCloud }}
if (!cloud) return "{{\\"error\\": \\"YAD cloud not found: {cloud_name}\\"}}"

def source = cloud.templates.find {{ it.id == "{source_template_id}" || it.labelString == "{source_template_id}" }}
if (!source) return "{{\\"error\\": \\"Source template not found: {source_template_id}\\"}}"

def existing = cloud.templates.find {{ it.labelString == "{new_label}" }}
if (existing) return "{{\\"error\\": \\"Template with label '{new_label}' already exists\\"}}"

// Create new template with full copy of lifecyle settings
def newId = UUID.randomUUID().toString()
def newTemplate = new DockerSlaveTemplate(newId)

def src = source
newTemplate.labelString = "{new_label}"
newTemplate.remoteFs = src.remoteFs
newTemplate.numExecutors = src.numExecutors
newTemplate.maxCapacity = src.maxCapacity
newTemplate.mode = src.mode
newTemplate.launcher = src.launcher
newTemplate.retentionStrategy = src.retentionStrategy
newTemplate.nodeProperties = src.nodeProperties

// Copy lifecycle
def srcLifecycle = src.dockerContainerLifecycle
if (srcLifecycle) {{
    def newLifecycle = new DockerContainerLifecycle()
    newLifecycle.image = srcLifecycle.image
    newLifecycle.pullImage = srcLifecycle.pullImage
    newLifecycle.stopContainer = srcLifecycle.stopContainer
    newLifecycle.removeContainer = srcLifecycle.removeContainer

    // Copy createContainer
    if (srcLifecycle.createContainer) {{
        def cc = srcLifecycle.createContainer
        def newCc = new DockerCreateContainer()
        newCc.command = cc.command
        newCc.commands = cc.commands
        newCc.entrypoint = cc.entrypoint
        newCc.hostname = cc.hostname
        newCc.user = cc.user
        newCc.workdir = cc.workdir
        newCc.memoryLimit = cc.memoryLimit
        newCc.cpuShares = cc.cpuShares
        newCc.cpusetCpus = cc.cpusetCpus
        newCc.cpusetMems = cc.cpusetMems
        newCc.privileged = cc.privileged
        newCc.tty = cc.tty
        newCc.networkMode = cc.networkMode
        newCc.volumes = cc.volumes
        newCc.volumesFrom = cc.volumesFrom
        newCc.environment = cc.environment
        newCc.bindPorts = cc.bindPorts
        newCc.bindAllPorts = cc.bindAllPorts
        newCc.dnsHosts = cc.dnsHosts
        newCc.extraHosts = cc.extraHosts
        newCc.devices = cc.devices
        newCc.shmSize = cc.shmSize
        newCc.macAddress = cc.macAddress
        newCc.links = cc.links
        newCc.dockerLabels = cc.dockerLabels
        newCc.restartPolicy = cc.restartPolicy
        newLifecycle.createContainer = newCc
    }}
    newTemplate.dockerContainerLifecycle = newLifecycle
}}

cloud.templates.add(newTemplate)
Jenkins.getInstance().save()
return "{{\\"success\\": true, \\"id\\": \\"" + newId + "\\", \\"label\\": \\"{new_label}\\"}}"
'''
    try:
        result = _run_groovy(jk, script)
        return json.loads(result)
    except Exception as e:
        raise JenkinsException(f'Failed to copy YAD template: {e}')
