"""
Kubernetes Plugin (kubernetes-plugin) 云管理模块

支持对Jenkins kubernetes-plugin的云管理:
- 查看Kubernetes云配置
- 创建/更新/删除Kubernetes云
- 查看Pod模板
- 添加/更新/删除Pod模板
- 复制Pod模板
"""

import json
from typing import Optional

from jenkins_mcp.jenkins import Jenkins, JenkinsException


def _run_groovy(jk, script: str) -> str:
    return jk.run_script(script)


async def get_kubernetes_clouds(jk: Jenkins) -> list:
    """获取所有Kubernetes云配置列表"""
    script = '''
import org.csanchez.jenkins.plugins.kubernetes.KubernetesCloud
import jenkins.model.Jenkins
import groovy.json.JsonOutput

def result = []
Jenkins.getInstance().clouds.each { cloud ->
    if (cloud instanceof KubernetesCloud) {
        result << [
            name: cloud.name,
            serverUrl: cloud.serverUrl ?: '',
            namespace: cloud.namespace ?: '',
            containerCap: cloud.containerCap ?: 0,
            templateCount: cloud.templates?.size() ?: 0,
            webSocket: cloud.webSocket ?: false
        ]
    }
}
return JsonOutput.toJson(result)
'''
    try:
        result = _run_groovy(jk, script)
        return json.loads(result)
    except Exception as e:
        raise JenkinsException(f'Failed to get Kubernetes clouds: {e}')


async def get_kubernetes_cloud(jk: Jenkins, cloud_name: str) -> Optional[dict]:
    """获取指定Kubernetes云配置详情"""
    script = f'''
import org.csanchez.jenkins.plugins.kubernetes.KubernetesCloud
import org.csanchez.jenkins.plugins.kubernetes.PodTemplate
import org.csanchez.jenkins.plugins.kubernetes.ContainerTemplate
import org.csanchez.jenkins.plugins.kubernetes.PodAnnotation
import org.csanchez.jenkins.plugins.kubernetes.PodLabel
import org.csanchez.jenkins.plugins.kubernetes.PodImagePullSecret
import org.csanchez.jenkins.plugins.kubernetes.TemplateEnvVar
import org.csanchez.jenkins.plugins.kubernetes.model.KeyValueEnvVar
import org.csanchez.jenkins.plugins.kubernetes.model.SecretEnvVar
import jenkins.model.Jenkins
import groovy.json.JsonOutput

def cloud = Jenkins.getInstance().clouds.find {{ it.name == "{cloud_name}" && it instanceof KubernetesCloud }}
if (!cloud) return "null"

def gp = {{ obj, prop, defVal = null ->
    try {{ return obj != null && obj.hasProperty(prop) ? obj."$prop" : defVal }} catch (Exception e) {{ return defVal }}
}}

def serializeEnvVars = {{ envVars ->
    (envVars ?: []).collect {{ ev ->
        if (ev instanceof KeyValueEnvVar) {{
            return [type: "keyValue", key: ev.key, value: ev.value]
        }} else if (ev instanceof SecretEnvVar) {{
            return [type: "secret", key: ev.key, secretName: ev.secretName, secretKey: ev.secretKey]
        }} else {{
            return [type: "unknown", key: gp(ev, 'key', '')]
        }}
    }}
}}

def templates = (cloud.templates ?: []).collect {{ t ->
    def containers = (t.containers ?: []).collect {{ c ->
        [
            name: gp(c, 'name', ''),
            image: gp(c, 'image', ''),
            command: gp(c, 'command', ''),
            args: gp(c, 'args', ''),
            workingDir: gp(c, 'workingDir', '/home/jenkins/agent'),
            ttyEnabled: gp(c, 'ttyEnabled', false),
            privileged: gp(c, 'privileged', false),
            alwaysPullImage: gp(c, 'alwaysPullImage', false),
            resourceRequestCpu: gp(c, 'resourceRequestCpu', '') ?: '',
            resourceRequestMemory: gp(c, 'resourceRequestMemory', '') ?: '',
            resourceLimitCpu: gp(c, 'resourceLimitCpu', '') ?: '',
            resourceLimitMemory: gp(c, 'resourceLimitMemory', '') ?: '',
            resourceRequestEphemeralStorage: gp(c, 'resourceRequestEphemeralStorage', '') ?: '',
            resourceLimitEphemeralStorage: gp(c, 'resourceLimitEphemeralStorage', '') ?: '',
            shell: gp(c, 'shell', '') ?: '',
            envVars: serializeEnvVars(gp(c, 'envVars', [])),
            ports: gp(c, 'ports', []).collect {{ p ->
                [name: gp(p, 'name', ''), containerPort: gp(p, 'containerPort', 0), hostPort: gp(p, 'hostPort', 0)]
            }}
        ]
    }}

    def volumes = (t.volumes ?: []).collect {{ v ->
        [
            type: v.class.simpleName,
            mountPath: gp(v, 'mountPath', ''),
            hostPath: gp(v, 'hostPath', ''),
            secretName: gp(v, 'secretName', ''),
            claimName: gp(v, 'claimName', '')
        ]
    }}

    [
        name: gp(t, 'name', ''),
        label: gp(t, 'label', ''),
        instanceCap: gp(t, 'instanceCap', Integer.MAX_VALUE),
        containers: containers,
        volumes: volumes,
        envVars: serializeEnvVars(gp(t, 'envVars', [])),
        imagePullSecrets: (t.imagePullSecrets ?: []).collect {{ [name: gp(it, 'name', '')] }},
        annotations: (t.annotations ?: []).collect {{ [key: gp(it, 'key', ''), value: gp(it, 'value', '')] }},
        nodeSelector: gp(t, 'nodeSelector', ''),
        serviceAccount: gp(t, 'serviceAccount', ''),
        hostNetwork: gp(t, 'hostNetwork', false),
        idleMinutes: gp(t, 'idleMinutes', 0),
        activeDeadlineSeconds: gp(t, 'activeDeadlineSeconds', 0),
        yaml: gp(t, 'yaml', ''),
        yamlMergeStrategy: gp(t, 'yamlMergeStrategy', null)?.class?.simpleName ?: '',
        slaveConnectTimeout: gp(t, 'slaveConnectTimeout', 1000),
        inheritFrom: gp(t, 'inheritFrom', ''),
        workspaceVolume: gp(t, 'workspaceVolume', null)?.class?.simpleName ?: '',
        podRetention: gp(t, 'podRetention', null)?.class?.simpleName ?: '',
        runAsUser: gp(t, 'runAsUser', null),
        runAsGroup: gp(t, 'runAsGroup', null),
        supplementalGroups: gp(t, 'supplementalGroups', ''),
        namespace: gp(t, 'namespace', '')
    ]
}}

def result = [
    name: cloud.name,
    class: cloud.class.name,
    serverUrl: cloud.serverUrl ?: '',
    serverCertificate: cloud.serverCertificate ?: '',
    skipTlsVerify: cloud.skipTlsVerify ?: false,
    namespace: cloud.namespace ?: '',
    jenkinsUrl: cloud.jenkinsUrl ?: '',
    jenkinsTunnel: cloud.jenkinsTunnel ?: '',
    credentialsId: cloud.credentialsId ?: '',
    containerCap: cloud.containerCap ?: 0,
    maxRequestsPerHost: cloud.maxRequestsPerHost ?: 32,
    connectTimeout: cloud.connectTimeout ?: 5,
    readTimeout: cloud.readTimeout ?: 15,
    retentionTimeout: cloud.retentionTimeout ?: 5,
    waitForPodSec: cloud.waitForPodSec ?: 600,
    webSocket: cloud.webSocket ?: false,
    directConnection: cloud.directConnection ?: false,
    podRetention: cloud.podRetention?.class?.simpleName ?: '',
    templates: templates
]
return JsonOutput.toJson(result)
'''
    try:
        result = _run_groovy(jk, script)
        return json.loads(result) if result else None
    except Exception as e:
        raise JenkinsException(f'Failed to get Kubernetes cloud: {e}')


async def create_kubernetes_cloud(
    jk: Jenkins,
    name: str,
    server_url: str,
    namespace: str = 'default',
    credentials_id: str = '',
    container_cap: int = 0,
    skip_tls_verify: bool = False,
    jenkins_url: str = '',
    web_socket: bool = False
) -> dict:
    """创建Kubernetes云配置"""
    skip_tls = 'true' if skip_tls_verify else 'false'
    ws = 'true' if web_socket else 'false'
    lines = []
    lines.append('def cloud = new KubernetesCloud("' + name + '")')
    lines.append('cloud.serverUrl = "' + server_url + '"')
    lines.append('cloud.namespace = "' + namespace + '"')
    lines.append('cloud.skipTlsVerify = ' + skip_tls)
    lines.append('cloud.webSocket = ' + ws)
    lines.append('cloud.containerCap = ' + str(container_cap))
    if jenkins_url:
        lines.append('cloud.jenkinsUrl = "' + jenkins_url + '"')
    if credentials_id:
        lines.append('cloud.credentialsId = "' + credentials_id + '"')
    lines.append('')
    lines.append('Jenkins.getInstance().clouds.add(cloud)')
    lines.append('Jenkins.getInstance().save()')
    lines.append('return "{\\"success\\": true, \\"name\\": \\"' + name + '\\"}"')

    script = '''import org.csanchez.jenkins.plugins.kubernetes.KubernetesCloud
import jenkins.model.Jenkins

def existing = Jenkins.getInstance().clouds.find { it.name == "''' + name + '''" && it instanceof KubernetesCloud }
if (existing) return "{\\"error\\": \\"Kubernetes cloud already exists: ''' + name + '''\\"}"
'''
    script += '\n'.join(lines)
    try:
        result = _run_groovy(jk, script)
        return json.loads(result)
    except Exception as e:
        raise JenkinsException(f'Failed to create Kubernetes cloud: {e}')


async def delete_kubernetes_cloud(jk: Jenkins, cloud_name: str) -> dict:
    """删除Kubernetes云配置"""
    script = f'''
import org.csanchez.jenkins.plugins.kubernetes.KubernetesCloud
import jenkins.model.Jenkins

def cloud = Jenkins.getInstance().clouds.find {{ it.name == "{cloud_name}" && it instanceof KubernetesCloud }}
if (!cloud) return "{{\\"error\\": \\"Kubernetes cloud not found: {cloud_name}\\"}}"

Jenkins.getInstance().clouds.remove(cloud)
Jenkins.getInstance().save()
return "{{\\"success\\": true, \\"name\\": \\"{cloud_name}\\"}}"
'''
    try:
        result = _run_groovy(jk, script)
        return json.loads(result)
    except Exception as e:
        raise JenkinsException(f'Failed to delete Kubernetes cloud: {e}')


async def get_pod_templates(jk: Jenkins, cloud_name: str) -> list:
    """获取Kubernetes云的所有Pod模板列表"""
    script = f'''
import org.csanchez.jenkins.plugins.kubernetes.KubernetesCloud
import jenkins.model.Jenkins
import groovy.json.JsonOutput

def cloud = Jenkins.getInstance().clouds.find {{ it.name == "{cloud_name}" && it instanceof KubernetesCloud }}
if (!cloud) return "[]"

def gp = {{ obj, prop, defVal = null ->
    try {{ return obj != null && obj.hasProperty(prop) ? obj."$prop" : defVal }} catch (Exception e) {{ return defVal }}
}}

def result = (cloud.templates ?: []).collect {{ t ->
    [
        name: gp(t, 'name', ''),
        label: gp(t, 'label', ''),
        image: t.containers?.size() > 0 ? gp(t.containers[0], 'image', '') : '',
        instanceCap: gp(t, 'instanceCap', Integer.MAX_VALUE),
        containerCount: t.containers?.size() ?: 0,
        volumeCount: t.volumes?.size() ?: 0,
        namespace: gp(t, 'namespace', ''),
        inheritFrom: gp(t, 'inheritFrom', '')
    ]
}}
return JsonOutput.toJson(result)
'''
    try:
        result = _run_groovy(jk, script)
        return json.loads(result)
    except Exception as e:
        raise JenkinsException(f'Failed to get pod templates: {e}')


async def get_pod_template(jk: Jenkins, cloud_name: str, template_name: str) -> Optional[dict]:
    """获取指定Pod模板详情"""
    script = f'''
import org.csanchez.jenkins.plugins.kubernetes.KubernetesCloud
import org.csanchez.jenkins.plugins.kubernetes.PodTemplate
import org.csanchez.jenkins.plugins.kubernetes.ContainerTemplate
import org.csanchez.jenkins.plugins.kubernetes.TemplateEnvVar
import org.csanchez.jenkins.plugins.kubernetes.model.KeyValueEnvVar
import org.csanchez.jenkins.plugins.kubernetes.model.SecretEnvVar
import jenkins.model.Jenkins
import groovy.json.JsonOutput

def cloud = Jenkins.getInstance().clouds.find {{ it.name == "{cloud_name}" && it instanceof KubernetesCloud }}
if (!cloud) return "null"

def t = cloud.templates.find {{ it.name == "{template_name}" }}
if (!t) return "null"

def gp = {{ obj, prop, defVal = null ->
    try {{ return obj != null && obj.hasProperty(prop) ? obj."$prop" : defVal }} catch (Exception e) {{ return defVal }}
}}

def serializeEnvVars = {{ envVars ->
    (envVars ?: []).collect {{ ev ->
        if (ev instanceof KeyValueEnvVar) {{
            return [type: "keyValue", key: ev.key, value: ev.value]
        }} else if (ev instanceof SecretEnvVar) {{
            return [type: "secret", key: ev.key, secretName: ev.secretName, secretKey: ev.secretKey]
        }} else {{
            return [type: "unknown", key: gp(ev, 'key', '')]
        }}
    }}
}}

def containers = (t.containers ?: []).collect {{ c ->
    [
        name: gp(c, 'name', ''),
        image: gp(c, 'image', ''),
        command: gp(c, 'command', ''),
        args: gp(c, 'args', ''),
        workingDir: gp(c, 'workingDir', '/home/jenkins/agent'),
        ttyEnabled: gp(c, 'ttyEnabled', false),
        privileged: gp(c, 'privileged', false),
        alwaysPullImage: gp(c, 'alwaysPullImage', false),
        resourceRequestCpu: gp(c, 'resourceRequestCpu', '') ?: '',
        resourceRequestMemory: gp(c, 'resourceRequestMemory', '') ?: '',
        resourceLimitCpu: gp(c, 'resourceLimitCpu', '') ?: '',
        resourceLimitMemory: gp(c, 'resourceLimitMemory', '') ?: '',
        resourceRequestEphemeralStorage: gp(c, 'resourceRequestEphemeralStorage', '') ?: '',
        resourceLimitEphemeralStorage: gp(c, 'resourceLimitEphemeralStorage', '') ?: '',
        shell: gp(c, 'shell', '') ?: '',
        envVars: serializeEnvVars(gp(c, 'envVars', [])),
        ports: gp(c, 'ports', []).collect {{ p ->
            [name: gp(p, 'name', ''), containerPort: gp(p, 'containerPort', 0), hostPort: gp(p, 'hostPort', 0)]
        }}
    ]
}}

def volumes = (t.volumes ?: []).collect {{ v ->
    [
        type: v.class.simpleName,
        mountPath: gp(v, 'mountPath', ''),
        hostPath: gp(v, 'hostPath', ''),
        secretName: gp(v, 'secretName', ''),
        claimName: gp(v, 'claimName', ''),
        configMapName: gp(v, 'configMapName', ''),
        readOnly: gp(v, 'readOnly', false)
    ]
}}

def result = [
    name: gp(t, 'name', ''),
    label: gp(t, 'label', ''),
    instanceCap: gp(t, 'instanceCap', Integer.MAX_VALUE),
    namespace: gp(t, 'namespace', ''),
    inheritFrom: gp(t, 'inheritFrom', ''),
    nodeSelector: gp(t, 'nodeSelector', ''),
    serviceAccount: gp(t, 'serviceAccount', ''),
    hostNetwork: gp(t, 'hostNetwork', false),
    idleMinutes: gp(t, 'idleMinutes', 0),
    activeDeadlineSeconds: gp(t, 'activeDeadlineSeconds', 0),
    slaveConnectTimeout: gp(t, 'slaveConnectTimeout', 1000),
    yaml: gp(t, 'yaml', ''),
    yamlMergeStrategy: gp(t, 'yamlMergeStrategy', null)?.class?.simpleName ?: '',
    runAsUser: gp(t, 'runAsUser', null),
    runAsGroup: gp(t, 'runAsGroup', null),
    supplementalGroups: gp(t, 'supplementalGroups', ''),
    containers: containers,
    volumes: volumes,
    envVars: serializeEnvVars(gp(t, 'envVars', [])),
    imagePullSecrets: (t.imagePullSecrets ?: []).collect {{ [name: gp(it, 'name', '')] }},
    annotations: (t.annotations ?: []).collect {{ [key: gp(it, 'key', ''), value: gp(it, 'value', '')] }},
    workspaceVolume: gp(t, 'workspaceVolume', null)?.class?.simpleName ?: '',
    podRetention: gp(t, 'podRetention', null)?.class?.simpleName ?: '',
    agentContainer: gp(t, 'agentContainer', ''),
    readonlyFromUi: gp(t, 'readonlyFromUi', false)
]
return JsonOutput.toJson(result)
'''
    try:
        result = _run_groovy(jk, script)
        return json.loads(result) if result else None
    except Exception as e:
        raise JenkinsException(f'Failed to get pod template: {e}')


async def add_pod_template(jk: Jenkins, cloud_name: str, template_config: dict) -> dict:
    """添加Pod模板到Kubernetes云

    参数:
        cloud_name: Kubernetes云名称
        template_config: 模板配置 {
            name: str (必填), containers: list (必填), label: str,
            volumes: list, envVars: list, imagePullSecrets: list,
            yaml: str, nodeSelector: str, serviceAccount: str,
            hostNetwork: bool, idleMinutes: int, instanceCap: int,
            podRetention: str, inheritFrom: str, namespace: str
        }
    """
    import json as _json
    config_json = _json.dumps(template_config)

    script = f'''
import org.csanchez.jenkins.plugins.kubernetes.KubernetesCloud
import org.csanchez.jenkins.plugins.kubernetes.PodTemplate
import org.csanchez.jenkins.plugins.kubernetes.ContainerTemplate
import org.csanchez.jenkins.plugins.kubernetes.model.KeyValueEnvVar
import jenkins.model.Jenkins
import groovy.json.JsonSlurper

def cloud = Jenkins.getInstance().clouds.find {{ it.name == "{cloud_name}" && it instanceof KubernetesCloud }}
if (!cloud) return "{{\\"error\\": \\"Kubernetes cloud not found: {cloud_name}\\"}}"

def config = new JsonSlurper().parseText(''' + _json.dumps(config_json) + ''')

if (!config.name) return "{{\\"error\\": \\"Template name is required\\"}}"

def existing = cloud.templates.find {{ it.name == config.name }}
if (existing) return "{{\\"error\\": \\"Pod template already exists: " + config.name + "\\"}}"

def template = new PodTemplate(config.name)
template.label = config.label ?: ""
template.instanceCap = (config.instanceCap ?: Integer.MAX_VALUE) as int
template.namespace = config.namespace ?: ""
template.inheritFrom = config.inheritFrom ?: ""
template.nodeSelector = config.nodeSelector ?: ""
template.serviceAccount = config.serviceAccount ?: ""
template.hostNetwork = config.hostNetwork ?: false
template.idleMinutes = (config.idleMinutes ?: 0) as int
template.yaml = config.yaml ?: ""
if (config.podRetention) {{
    def retentions = org.csanchez.jenkins.plugins.kubernetes.pod.retention.PodRetention.all()
    template.podRetention = retentions.find {{ it.class.simpleName == config.podRetention }}
}}

if (config.containers) {{
    def containers = config.containers.collect {{ c ->
        def ct = new ContainerTemplate(c.name ?: "", c.image ?: "")
        ct.command = c.command ?: ""
        ct.args = c.args ?: ""
        ct.workingDir = c.workingDir ?: "/home/jenkins/agent"
        ct.ttyEnabled = c.ttyEnabled ?: false
        ct.privileged = c.privileged ?: false
        ct.alwaysPullImage = c.alwaysPullImage ?: false
        ct.resourceRequestCpu = c.resourceRequestCpu ?: ""
        ct.resourceRequestMemory = c.resourceRequestMemory ?: ""
        ct.resourceLimitCpu = c.resourceLimitCpu ?: ""
        ct.resourceLimitMemory = c.resourceLimitMemory ?: ""
        ct.resourceRequestEphemeralStorage = c.resourceRequestEphemeralStorage ?: ""
        ct.resourceLimitEphemeralStorage = c.resourceLimitEphemeralStorage ?: ""
        ct.shell = c.shell ?: ""
        if (c.envVars) {{
            c.envVars.each {{ ev ->
                if (ev.type == "keyValue") {{
                    ct.envVars.add(new KeyValueEnvVar(ev.key, ev.value ?: ""))
                }}
            }}
        }}
        return ct
    }}
    template.containers = containers
}}

cloud.templates.add(template)
Jenkins.getInstance().save()
return "{{\\"success\\": true, \\"name\\": \\"" + config.name + "\\"}}"
'''
    try:
        result = _run_groovy(jk, script)
        return json.loads(result)
    except Exception as e:
        raise JenkinsException(f'Failed to add pod template: {e}')


async def update_pod_template(jk: Jenkins, cloud_name: str, template_name: str, template_config: dict) -> dict:
    """更新Kubernetes Pod模板

    参数:
        cloud_name: Kubernetes云名称
        template_name: 模板名称
        template_config: 要更新的字段 {
            label: str, instanceCap: int, namespace: str,
            inheritFrom: str, nodeSelector: str, serviceAccount: str,
            hostNetwork: bool, idleMinutes: int, yaml: str,
            podRetention: str, containers: list
        }
    """
    import json as _json
    updates = _json.dumps(template_config)

    script = f'''
import org.csanchez.jenkins.plugins.kubernetes.KubernetesCloud
import org.csanchez.jenkins.plugins.kubernetes.PodTemplate
import org.csanchez.jenkins.plugins.kubernetes.ContainerTemplate
import org.csanchez.jenkins.plugins.kubernetes.model.KeyValueEnvVar
import jenkins.model.Jenkins
import groovy.json.JsonSlurper

def cloud = Jenkins.getInstance().clouds.find {{ it.name == "{cloud_name}" && it instanceof KubernetesCloud }}
if (!cloud) return "{{\\"error\\": \\"Kubernetes cloud not found: {cloud_name}\\"}}"

def t = cloud.templates.find {{ it.name == "{template_name}" }}
if (!t) return "{{\\"error\\": \\"Pod template not found: {template_name}\\"}}"

def updates = new JsonSlurper().parseText(''' + _json.dumps(updates) + ''')

if (updates.containsKey("label")) t.label = updates.label ?: ""
if (updates.containsKey("instanceCap")) t.instanceCap = (updates.instanceCap ?: Integer.MAX_VALUE) as int
if (updates.containsKey("namespace")) t.namespace = updates.namespace ?: ""
if (updates.containsKey("inheritFrom")) t.inheritFrom = updates.inheritFrom ?: ""
if (updates.containsKey("nodeSelector")) t.nodeSelector = updates.nodeSelector ?: ""
if (updates.containsKey("serviceAccount")) t.serviceAccount = updates.serviceAccount ?: ""
if (updates.containsKey("hostNetwork")) t.hostNetwork = updates.hostNetwork as boolean
if (updates.containsKey("idleMinutes")) t.idleMinutes = (updates.idleMinutes ?: 0) as int
if (updates.containsKey("yaml")) t.yaml = updates.yaml ?: ""
if (updates.containsKey("podRetention")) {{
    def retentions = org.csanchez.jenkins.plugins.kubernetes.pod.retention.PodRetention.all()
    def retention = retentions.find {{ it.class.simpleName == updates.podRetention }}
    if (retention) t.podRetention = retention
}}
if (updates.containsKey("containers")) {{
    def containers = updates.containers.collect {{ c ->
        def ct = new ContainerTemplate(c.name ?: "", c.image ?: "")
        ct.command = c.command ?: ""
        ct.args = c.args ?: ""
        ct.workingDir = c.workingDir ?: "/home/jenkins/agent"
        ct.ttyEnabled = c.ttyEnabled ?: false
        ct.privileged = c.privileged ?: false
        ct.alwaysPullImage = c.alwaysPullImage ?: false
        ct.resourceRequestCpu = c.resourceRequestCpu ?: ""
        ct.resourceRequestMemory = c.resourceRequestMemory ?: ""
        ct.resourceLimitCpu = c.resourceLimitCpu ?: ""
        ct.resourceLimitMemory = c.resourceLimitMemory ?: ""
        ct.resourceRequestEphemeralStorage = c.resourceRequestEphemeralStorage ?: ""
        ct.resourceLimitEphemeralStorage = c.resourceLimitEphemeralStorage ?: ""
        ct.shell = c.shell ?: ""
        if (c.envVars) {{
            c.envVars.each {{ ev ->
                if (ev.type == "keyValue") {{
                    ct.envVars.add(new KeyValueEnvVar(ev.key, ev.value ?: ""))
                }}
            }}
        }}
        return ct
    }}
    t.containers = containers
}}

Jenkins.getInstance().save()
return "{{\\"success\\": true, \\"name\\": \\"{template_name}\\"}}"
'''
    try:
        result = _run_groovy(jk, script)
        return json.loads(result)
    except Exception as e:
        raise JenkinsException(f'Failed to update pod template: {e}')


async def delete_pod_template(jk: Jenkins, cloud_name: str, template_name: str) -> dict:
    """删除Kubernetes云中的Pod模板"""
    script = f'''
import org.csanchez.jenkins.plugins.kubernetes.KubernetesCloud
import jenkins.model.Jenkins

def cloud = Jenkins.getInstance().clouds.find {{ it.name == "{cloud_name}" && it instanceof KubernetesCloud }}
if (!cloud) return "{{\\"error\\": \\"Kubernetes cloud not found: {cloud_name}\\"}}"

def t = cloud.templates.find {{ it.name == "{template_name}" }}
if (!t) return "{{\\"error\\": \\"Pod template not found: {template_name}\\"}}"

cloud.templates.remove(t)
Jenkins.getInstance().save()
return "{{\\"success\\": true, \\"name\\": \\"{template_name}\\"}}"
'''
    try:
        result = _run_groovy(jk, script)
        return json.loads(result)
    except Exception as e:
        raise JenkinsException(f'Failed to delete pod template: {e}')


async def copy_pod_template(jk: Jenkins, cloud_name: str, source_template_name: str, new_template_name: str) -> dict:
    """复制Kubernetes Pod模板

    使用PodTemplate的XStream拷贝构造函数进行深度复制
    """
    script = f'''
import org.csanchez.jenkins.plugins.kubernetes.KubernetesCloud
import org.csanchez.jenkins.plugins.kubernetes.PodTemplate
import jenkins.model.Jenkins

def cloud = Jenkins.getInstance().clouds.find {{ it.name == "{cloud_name}" && it instanceof KubernetesCloud }}
if (!cloud) return "{{\\"error\\": \\"Kubernetes cloud not found: {cloud_name}\\"}}"

def source = cloud.templates.find {{ it.name == "{source_template_name}" }}
if (!source) return "{{\\"error\\": \\"Source pod template not found: {source_template_name}\\"}}"

def existing = cloud.templates.find {{ it.name == "{new_template_name}" }}
if (existing) return "{{\\"error\\": \\"Pod template already exists: {new_template_name}\\"}}"

// Use XStream copy constructor via XML roundtrip to create deep copy
def xstream = new com.thoughtworks.xstream.XStream()
xstream.setClassLoader(source.class.classLoader)
def xml = xstream.toXML(source)
def copy = xstream.fromXML(xml) as PodTemplate
copy.name = "{new_template_name}"

cloud.templates.add(copy)
Jenkins.getInstance().save()
return "{{\\"success\\": true, \\"name\\": \\"{new_template_name}\\"}}"
'''
    try:
        result = _run_groovy(jk, script)
        return json.loads(result)
    except Exception as e:
        raise JenkinsException(f'Failed to copy pod template: {e}')
