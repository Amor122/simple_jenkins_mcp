"""
Jenkins MCP Server - Cloud管理工具模块 (基于Groovy)

提供完整的云配置管理功能:
- 配置读取
- 节点分析
- 可用性分析
- 配置修改
- 新建云类型
- 新建云模板
"""

from jenkins_mcp.jenkins import JenkinsException
from jenkins_mcp.tools.utils import admin_only, write_only


def _run_groovy(jk, script: str) -> str:
    """执行Groovy脚本并返回结果"""
    return jk.run_script(script)


# ==================== 配置读取 ====================

@write_only
async def get_all_clouds(jk) -> list:
    """获取所有云配置

    返回所有配置的云，包括Kubernetes、Docker等

    返回:
    云配置列表
    """

    script = '''
import hudson.slaves.Cloud
import jenkins.model.Jenkins
import groovy.json.JsonOutput

def clouds = []
Jenkins.getInstance().clouds.toList().each { cloud ->
    def config = new java.util.LinkedHashMap()
    try {
        config["name"] = cloud.name.toString()
    } catch (Exception e) {
        config["name"] = "unknown"
    }
    config["class"] = cloud.class.name
    config["disabled"] = false

    def templates = []
    if (cloud.hasProperty("templates") && cloud.templates != null) {
        cloud.templates.each { t ->
            def tmpl = new java.util.LinkedHashMap()
            tmpl["name"] = t.hasProperty("name") ? (t.name != null ? t.name.toString() : "") : ""
            tmpl["label"] = ""
            tmpl["image"] = ""
            tmpl["containers"] = []
            tmpl["volumes"] = []
            templates << tmpl
        }
    }
    config["templates"] = templates
    clouds << config
}
return JsonOutput.toJson(clouds)
'''
    try:
        result = _run_groovy(jk, script)
        import json
        return json.loads(result)
    except Exception as e:
        raise JenkinsException(f'Failed to get clouds: {e}')


@write_only
async def get_cloud_config(jk, name: str) -> dict:
    """获取指定云配置的详细信息
    
    参数:
        name: 云名称
    
    返回:
        云配置详情
    """
    
    script = f'''
import hudson.slaves.Cloud
import jenkins.model.Jenkins
import groovy.json.JsonOutput

def cloud = Jenkins.getInstance().clouds.find {{ it.name == "{name}" }}
if (!cloud) {{
    return "{{\\"error\\": \\"Cloud not found: {name}\\"}}"
}}

def gp = {{ obj, prop, defVal = null ->
    obj != null && obj.hasProperty(prop) ? obj."$prop" : defVal
}}

def gl = {{ list, defVal = [] ->
    list != null ? list : defVal
}}

def config = [
    name: cloud.name,
    class: cloud.class.name
]

// Kubernetes Cloud specific
if (cloud.class.name == 'org.csanchez.jenkins.plugins.kubernetes.KubernetesCloud') {{
    config.serverUrl = gp(cloud, 'serverUrl', '')
    config.serverCertificate = gp(cloud, 'serverCertificate', '') ?: ''
    config.skipTlsVerify = gp(cloud, 'skipTlsVerify', false)
    config.namespace = gp(cloud, 'namespace', 'default') ?: 'default'
    config.jenkinsUrl = gp(cloud, 'jenkinsUrl', '') ?: ''
    config.jenkinsTunnel = gp(cloud, 'jenkinsTunnel', '') ?: ''
    config.containerCap = gp(cloud, 'containerCap', 0)
    config.connectTimeout = gp(cloud, 'connectTimeout', 5)
    config.readTimeout = gp(cloud, 'readTimeout', 15)
    config.retentionTimeout = gp(cloud, 'retentionTimeout', 5)
    config.webSocket = gp(cloud, 'webSocket', false)
    config.directConnection = gp(cloud, 'directConnection', '') ?: ''
    config.credentialsId = gp(cloud, 'credentialsId', '') ?: ''
    config.maxRequestsPerHost = gp(cloud, 'maxRequestsPerHost', 32)
    
    // Pod templates
    config.templates = cloud.templates.collect {{ t ->
        def containersList = gl(gp(t, 'containers', null), [])
        def volumesList = gl(gp(t, 'volumes', null), [])
        def envVarsMap = gl(gp(t, 'envVars', null), [])
        def labelsMapObj = gl(gp(t, 'labelsMap', null), null)
        
        [
            name: gp(t, 'name', ''),
            label: gp(t, 'label', '') ?: '',
            image: gp(t, 'image', '') ?: '',
            remoteFs: gp(t, 'remoteFs', '') ?: '',
            instanceCap: gp(t, 'instanceCap', 0),
            nodeUsageMode: gp(t, 'nodeUsageMode', '')?.toString() ?: '',
            nodeSelector: gp(t, 'nodeSelector', [:]) ?: [:],
            serviceAccount: gp(t, 'serviceAccount', '') ?: '',
            yaml: gp(t, 'yaml', '') ?: '',
            envVars: (envVarsMap instanceof List ? envVarsMap.collect {{ [key: it.key?.toString(), value: it.value?.toString()] }} : []),
            labelsMap: (labelsMapObj != null ? labelsMapObj.collect {{ [key: it.key?.toString(), value: it.value?.toString()] }} : []),
            // Containers
            containers: containersList.collect {{ c ->
                [
                    image: gp(c, 'image', '') ?: '',
                    workingDir: gp(c, 'workingDir', '') ?: '',
                    command: gp(c, 'command', []) ? gp(c, 'command', []).join(' ') : '',
                    args: gp(c, 'args', '') ?: '',
                    shell: gp(c, 'shell', '') ?: '',
                    ttyEnabled: gp(c, 'ttyEnabled', false),
                    resourceRequestCpu: gp(c, 'resourceRequestCpu', '') ?: '',
                    resourceRequestMemory: gp(c, 'resourceRequestMemory', '') ?: '',
                    resourceLimitCpu: gp(c, 'resourceLimitCpu', '') ?: '',
                    resourceLimitMemory: gp(c, 'resourceLimitMemory', '') ?: ''
                ]
            }},
            // Volumes
            volumes: volumesList.collect {{ v ->
                [
                    type: v.class.simpleName,
                    mountPath: gp(v, 'mountPath', '') ?: '',
                    hostPath: gp(v, 'hostPath', '') ?: '',
                    secretName: gp(v, 'secretName', '') ?: '',
                    configMapName: gp(v, 'configMapName', '') ?: ''
                ]
            }}
        ]
    }}
    
    // Pod retention
    config.podRetention = gp(cloud, 'podRetention', null)?.class?.simpleName
}}

return JsonOutput.toJson(config)
'''
    try:
        result = _run_groovy(jk, script)
        import json
        return json.loads(result)
    except Exception as e:
        raise JenkinsException(f'Failed to get cloud config for {name}: {e}')


@write_only
async def get_cloud_templates(jk, cloud_name: str) -> list:
    """获取云的所有模板
    
    参数:
        cloud_name: 云名称
    
    返回:
        模板列表
    """
    
    script = f'''
import hudson.slaves.Cloud
import jenkins.model.Jenkins
import groovy.json.JsonOutput

def gp2 = {{ obj, prop, defVal = null ->
    obj != null && obj.hasProperty(prop) ? obj."$prop" : defVal
}}
def gl2 = {{ list, defVal = [] ->
    list != null ? list : defVal
}}

def cloud = Jenkins.getInstance().clouds.find {{ it.name == "{cloud_name}" }}
if (!cloud) {{
    return "[]"
}}

def templates = cloud.templates.collect {{ t ->
    [
        name: gp2(t, 'name', ''),
        label: gp2(t, 'label', '') ?: '',
        image: gp2(t, 'image', '') ?: '',
        remoteFs: gp2(t, 'remoteFs', '') ?: '',
        instanceCap: gp2(t, 'instanceCap', 0),
        nodeUsageMode: gp2(t, 'nodeUsageMode', '')?.toString() ?: ''
    ]
}}

return JsonOutput.toJson(templates)
'''
    try:
        result = _run_groovy(jk, script)
        import json
        return json.loads(result)
    except Exception as e:
        raise JenkinsException(f'Failed to get templates: {e}')


# ==================== 节点分析 ====================

@write_only
async def analyze_cloud_nodes(jk, cloud_name: str = None) -> dict:
    """分析云相关的节点
    
    参数:
        cloud_name: 可选，指定云名称
    
    返回:
        节点分析结果
    """
    
    if cloud_name:
        script = f'''
import hudson.slaves.Cloud
import hudson.model.Computer
import jenkins.model.Jenkins
import groovy.json.JsonOutput

def cloud = Jenkins.getInstance().clouds.find {{ it.name == "{cloud_name}" }}
if (!cloud) {{
    return "{{\\"error\\": \\"Cloud not found\\"}}"
}}

def nodeAnalysis = [
    cloud: cloud.name,
    cloudClass: cloud.class.simpleName,
    nodes: [],
    summary: [
        total: 0,
        online: 0,
        offline: 0,
        idle: 0,
        busy: 0,
        executors: 0,
        busyExecutors: 0
    ]
]

Jenkins.getInstance().computers.each {{ computer ->
    if (computer.node && computer.node.class.name != 'hudson.model.MasterControl') {{
        def isCloudNode = computer.node.class.name.contains('Kubernetes') || 
                          computer.node.class.name.contains('Docker') ||
                          computer.node.class.name.contains('Slave')
        
        if (isCloudNode) {{
            def node = [
                name: computer.name,
                displayName: computer.displayName,
                class: computer.node.class.simpleName,
                offline: computer.offline,
                idle: computer.idle,
                numExecutors: computer.numExecutors,
                busyExecutors: computer.busyExecutors,
                lastBuild: computer.lastBuild?.number,
                lastSuccessfulBuild: computer.lastSuccessfulBuild?.number,
                lastFailedBuild: computer.lastFailedBuild?.number,
                launchSupported: computer.launchSupported,
                temporarilyOffline: computer.temporarilyOffline
            ]
            nodeAnalysis.nodes << node
            nodeAnalysis.summary.total++
            if (!computer.offline) nodeAnalysis.summary.online++
            else nodeAnalysis.summary.offline++
            if (computer.idle) nodeAnalysis.summary.idle++
            else nodeAnalysis.summary.busy++
            nodeAnalysis.summary.executors += computer.numExecutors
            nodeAnalysis.summary.busyExecutors += computer.busyExecutors
        }}
    }}
}}

return JsonOutput.toJson(nodeAnalysis)
'''
    else:
        script = '''
import hudson.model.Computer
import jenkins.model.Jenkins
import groovy.json.JsonOutput

def nodeAnalysis = [
    clouds: [],
    summary: [
        totalNodes: 0,
        online: 0,
        offline: 0,
        idle: 0,
        busy: 0,
        totalExecutors: 0
    ]
]

// Group computers by cloud
def cloudNodes = [:]
Jenkins.getInstance().computers.each { computer ->
    if (computer.node && computer.node.class.name != 'hudson.model.MasterControl') {
        def node = [
            name: computer.name,
            displayName: computer.displayName,
            offline: computer.offline,
            idle: computer.idle,
            numExecutors: computer.numExecutors
        ]
        
        // Try to determine cloud source
        def cloudName = "Unknown"
        if (computer.node.hasProperty('cloud') && computer.node.cloud != null) {
            def c = computer.node.cloud
            cloudName = (c.hasProperty('name') ? c.name : 'CloudSet')
        } else {
            cloudName = "On-Premise"
        }
        
        if (!cloudNodes.containsKey(cloudName)) {
            cloudNodes[cloudName] = []
        }
        cloudNodes[cloudName] << node
        
        nodeAnalysis.summary.totalNodes++
        if (!computer.offline) nodeAnalysis.summary.online++
        else nodeAnalysis.summary.offline++
        if (computer.idle) nodeAnalysis.summary.idle++
        else nodeAnalysis.summary.busy++
        nodeAnalysis.summary.totalExecutors += computer.numExecutors
    }
}

cloudNodes.each { cloudName, nodes ->
    nodeAnalysis.clouds << [
        name: cloudName,
        nodes: nodes,
        count: nodes.size(),
        onlineCount: nodes.findAll { !it.offline }.size(),
        offlineCount: nodes.findAll { it.offline }.size()
    ]
}

return JsonOutput.toJson(nodeAnalysis)
'''
    try:
        result = _run_groovy(jk, script)
        import json
        return json.loads(result)
    except Exception as e:
        raise JenkinsException(f'Failed to analyze nodes: {e}')


@write_only
async def get_nodes_by_label(jk, label: str) -> list:
    """获取具有指定Label的所有节点（包括云节点）
    
    参数:
        label: Label名称
    
    返回:
        节点列表
    """
    
    script = f'''
import hudson.model.Label
import jenkins.model.Jenkins
import groovy.json.JsonOutput

def labelObj = Label.get("{label}")
def nodes = []

labelObj.nodes.each {{ node ->
    if (node.class.name != 'hudson.model.Hudson$MasterControl') {{
        nodes << [
            name: node.nodeName,
            displayName: node.displayName,
            class: node.class.simpleName,
            numExecutors: node.numExecutors,
            labelString: node.hasProperty('labelString') ? node.labelString : ''
        ]
    }}
}}

return JsonOutput.toJson(nodes)
'''
    try:
        result = _run_groovy(jk, script)
        import json
        return json.loads(result)
    except Exception as e:
        raise JenkinsException(f'Failed to get nodes by label: {e}')


# ==================== 可用性分析 ====================

@write_only
async def analyze_cloud_availability(jk, cloud_name: str = None) -> dict:
    """分析云可用性和健康状态
    
    参数:
        cloud_name: 可选，指定云名称
    
    返回:
        可用性分析结果
    """
    
    if cloud_name:
        script = f'''
import hudson.slaves.Cloud
import hudson.model.Computer
import jenkins.model.Jenkins
import groovy.json.JsonOutput

def cloud = Jenkins.getInstance().clouds.find {{ it.name == "{cloud_name}" }}
if (!cloud) {{
    return "{{\\"error\\": \\"Cloud not found\\"}}"
}}

def availability = [
    cloud: cloud.name,
    class: cloud.class.simpleName,
    healthy: true,
    issues: [],
    statistics: [
        totalCapacity: 0,
        currentUsage: 0,
        availableSlots: 0,
        provisionedPods: 0,
        pendingPods: 0,
        failedPods: 0
    ],
    nodeHealth: []
]

// Calculate capacity
if (cloud.hasProperty('containerCap')) {{
    availability.statistics.totalCapacity = cloud.containerCap
}}
if (cloud.hasProperty('templates')) {{
    def templateCaps = cloud.templates.sum {{ t -> t.instanceCap ?: 0 }}
    availability.statistics.totalCapacity = templateCaps
}}

// Analyze nodes
Jenkins.getInstance().computers.each {{ computer ->
    if (computer.node && !computer.offline) {{
        def isRelated = false
        if (computer.node.hasProperty('cloud')) {{
            def nodeCloud = computer.node.cloud
            if (nodeCloud != null && nodeCloud.hasProperty('name') && nodeCloud.name == cloud.name) {{
                isRelated = true
            }}
        }}
        
        if (isRelated) {{
            availability.statistics.currentUsage += computer.busyExecutors
            availability.statistics.availableSlots += computer.numExecutors - computer.busyExecutors
            
            availability.nodeHealth << [
                name: computer.name,
                online: true,
                idle: computer.idle,
                executors: computer.numExecutors,
                busy: computer.busyExecutors,
                lastActivity: computer.lastActivity
            ]
        }}
    }}
}}

availability.statistics.availableSlots = availability.statistics.totalCapacity - availability.statistics.provisionedPods

// Check for issues
if (availability.statistics.failedPods > 0) {{
    availability.healthy = false
    def fp = availability.statistics.failedPods
    availability.issues << "Failed pods detected: $fp"
}}
if (availability.statistics.pendingPods > 5) {{
    def pp = availability.statistics.pendingPods
    availability.issues << "High pending pod count: $pp"
}}

return JsonOutput.toJson(availability)
'''
    else:
        script = '''
import hudson.slaves.Cloud
import hudson.model.Computer
import jenkins.model.Jenkins
import groovy.json.JsonOutput

def availability = [
    clouds: [],
    systemHealth: [
        healthy: true,
        issues: []
    ]
]

Jenkins.getInstance().clouds.toList().each { cloud ->
    def cloudStatus = [
        name: cloud.name,
        class: cloud.class.simpleName,
        disabled: cloud.hasProperty('disabled') ? cloud.disabled : false,
        nodes: [],
        statistics: [
            totalCapacity: 0,
            online: 0,
            offline: 0,
            busy: 0,
            idle: 0
        ]
    ]
    
    // Count nodes by cloud
    Jenkins.getInstance().computers.each { computer ->
        if (computer.node && computer.node.class.name != 'hudson.model.MasterControl') {
            if (computer.node.hasProperty('cloud')) {
                def nodeCloud = computer.node.cloud
                if (nodeCloud != null && nodeCloud.hasProperty('name') && nodeCloud.name == cloud.name) {
                    cloudStatus.statistics.totalCapacity++
                    if (!computer.offline) {
                        cloudStatus.statistics.online++
                        if (computer.idle) cloudStatus.statistics.idle++
                        else cloudStatus.statistics.busy++
                    } else {
                        cloudStatus.statistics.offline++
                    }
                }
            }
        }
    }

    // Add cloud config capacity
    if (cloud.hasProperty('containerCap')) {
        cloudStatus.configCapacity = cloud.containerCap
    }
    
    availability.clouds << cloudStatus
}

// System-level health check
def pendingItems = Jenkins.getInstance().queue.items.size()
if (pendingItems > 10) {
    availability.systemHealth.issues << "High queue size: ${pendingItems}"
}

// Check for offline clouds
availability.clouds.each { c ->
    if (c.disabled) {
        availability.systemHealth.healthy = false
        availability.systemHealth.issues << "Cloud disabled: ${c.name}"
    }
}

return JsonOutput.toJson(availability)
'''
    try:
        result = _run_groovy(jk, script)
        import json
        return json.loads(result)
    except Exception as e:
        err_str = str(e)
        if 'StackOverflow' in err_str:
            return {
                "clouds": [],
                "systemHealth": {"healthy": True, "issues": ["StackOverflowError - too many nodes to analyze"]}
            }
        raise JenkinsException(f'Failed to analyze availability: {e}')


@write_only
async def get_provisioning_stats(jk) -> dict:
    """获取全局 Provisioning 统计信息
    
    返回:
        统计信息
    """
    
    script = '''
    import hudson.slaves.Cloud
    import jenkins.model.Jenkins
    import groovy.json.JsonOutput

    def ji = Jenkins.getInstance()
    def stats = [
    clouds: [],
    system: [
        mode: ji.hasProperty('mode') ? ji.mode?.toString() : '',
        numExecutors: ji.hasProperty('numExecutors') ? ji.numExecutors : 0,
        queueLength: ji.hasProperty('queueLength') ? ji.queueLength : 0
    ],
    summary: [
        totalClouds: 0,
        enabledClouds: 0,
        disabledClouds: 0,
        totalNodes: 0,
        onlineNodes: 0
    ]
    ]

    Jenkins.getInstance().clouds.toList().each { cloud ->
    def cloudStats = [
        name: cloud.name,
        class: cloud.class.simpleName,
        disabled: cloud.hasProperty('disabled') ? cloud.disabled : false,
        templates: cloud.templates?.size() ?: 0,
        containerCap: cloud.hasProperty('containerCap') ? cloud.containerCap : 0
    ]
    stats.clouds << cloudStats
    
    stats.summary.totalClouds++
    if (cloudStats.disabled) stats.summary.disabledClouds++
    else stats.summary.enabledClouds++
    }

    // Count online nodes
    Jenkins.getInstance().computers.each { computer ->
    if (computer.node && computer.node.class.name != 'hudson.model.MasterControl') {
        stats.summary.totalNodes++
        if (!computer.offline) stats.summary.onlineNodes++
    }
    }

    return JsonOutput.toJson(stats)
    '''
    try:
        result = _run_groovy(jk, script)
        import json
        return json.loads(result)
    except Exception as e:
        err_str = str(e)
        if 'StackOverflow' in err_str:
            return {
                "clouds": [],
                "system": {"mode": "", "numExecutors": 0, "queueLength": 0},
                "summary": {"totalClouds": 0, "enabledClouds": 0, "disabledClouds": 0, "totalNodes": 0, "onlineNodes": 0}
            }
        raise JenkinsException(f'Failed to get provisioning stats: {e}')


# ==================== 配置修改 ====================

@write_only
async def update_cloud_config(jk, cloud_name: str, config: dict) -> dict:
    """更新云配置
    
    参数:
        cloud_name: 云名称
        config: 配置字典
    
    返回:
        更新结果
    """
    
    raise JenkinsException(
        'Cloud配置修改需要通过Groovy脚本执行。'
        '请使用 run_groovy_script() 函数执行自定义Groovy脚本。'
    )


@write_only
async def disable_cloud(jk, cloud_name: str) -> dict:
    """禁用云
    
    参数:
        cloud_name: 云名称
    
    返回:
        执行结果
    """
    
    script = f'''
import hudson.slaves.Cloud
import jenkins.model.Jenkins

def cloud = Jenkins.getInstance().clouds.find {{ it.name == "{cloud_name}" }}
if (cloud) {{
    cloud.disabled = true
    Jenkins.getInstance().save()
    return "Cloud {cloud_name} has been disabled"
}} else {{
    return "Cloud {cloud_name} not found"
}}
'''
    try:
        result = _run_groovy(jk, script)
        return {"status": "success", "message": result}
    except Exception as e:
        raise JenkinsException(f'Failed to disable cloud: {e}')


@write_only
async def enable_cloud(jk, cloud_name: str) -> dict:
    """启用云
    
    参数:
        cloud_name: 云名称
    
    返回:
        执行结果
    """
    
    script = f'''
import hudson.slaves.Cloud
import jenkins.model.Jenkins

def cloud = Jenkins.getInstance().clouds.find {{ it.name == "{cloud_name}" }}
if (cloud) {{
    cloud.disabled = false
    Jenkins.getInstance().save()
    return "Cloud {cloud_name} has been enabled"
}} else {{
    return "Cloud {cloud_name} not found"
}}
'''
    try:
        result = _run_groovy(jk, script)
        return {"status": "success", "message": result}
    except Exception as e:
        raise JenkinsException(f'Failed to enable cloud: {e}')


@write_only
async def delete_cloud(jk, cloud_name: str) -> dict:
    """删除云配置
    
    参数:
        cloud_name: 云名称
    
    返回:
        执行结果
    """
    
    script = '''
import hudson.slaves.Cloud
import jenkins.model.Jenkins

def cloud = Jenkins.getInstance().clouds.find { it.name == "DELETE_CLOUD_PLACEHOLDER" }
if (cloud) {
    Jenkins.getInstance().clouds.remove(cloud)
    Jenkins.getInstance().save()
    return "Cloud DELETE_CLOUD_PLACEHOLDER deleted"
} else {
    return "Cloud DELETE_CLOUD_PLACEHOLDER not found"
}
'''.replace("DELETE_CLOUD_PLACEHOLDER", cloud_name)
    try:
        result = _run_groovy(jk, script)
        return {"status": "success", "message": result}
    except Exception as e:
        raise JenkinsException(f'Failed to delete cloud: {e}')


@write_only
async def delete_template(jk, cloud_name: str, template_name: str) -> dict:
    """删除云模板
    
    参数:
        cloud_name: 云名称
        template_name: 模板名称
    
    返回:
        执行结果
    """
    
    script = f'''
import hudson.slaves.Cloud
import jenkins.model.Jenkins

def cloud = Jenkins.getInstance().clouds.find {{ it.name == "{cloud_name}" }}
if (cloud) {{
    def template = cloud.templates.find {{ it.name == "{template_name}" }}
    if (template) {{
        cloud.templates.remove(template)
        Jenkins.getInstance().save()
        return "Template {template_name} deleted from cloud {cloud_name}"
    }} else {{
        return "Template {template_name} not found"
    }}
}} else {{
    return "Cloud {cloud_name} not found"
}}
'''
    try:
        result = _run_groovy(jk, script)
        return {"status": "success", "message": result}
    except Exception as e:
        raise JenkinsException(f'Failed to delete template: {e}')


# ==================== 新建云和模板 ====================

@write_only
async def create_kubernetes_cloud(jk, name: str, server_url: str, namespace: str = "default",
                                   credentials_id: str = None, container_cap: int = 0) -> dict:
    """创建Kubernetes云配置
    
    参数:
        name: 云名称
        server_url: Kubernetes API Server URL
        namespace: 命名空间
        credentials_id: 凭证ID
        container_cap: 容器上限
    
    返回:
        创建结果
    """
    
    script = f'''
import org.csanchez.jenkins.plugins.kubernetes.KubernetesCloud
import org.csanchez.jenkins.plugins.kubernetes.PodTemplate
import jenkins.model.Jenkins

def existing = Jenkins.getInstance().clouds.find {{ it.name == "{name}" }}
if (existing) {{
    return "Cloud {{name}} already exists"
}}

def cloud = new KubernetesCloud("{name}")
cloud.serverUrl = "{server_url}"
cloud.namespace = "{namespace}"
cloud.containerCap = {container_cap}
cloud.connectTimeout = 5
cloud.readTimeout = 15
cloud.retentionTimeout = 5
cloud.maxRequestsPerHost = 32

{(f'cloud.credentialsId = "{credentials_id}"' if credentials_id else '')}

Jenkins.getInstance().clouds.add(cloud)
Jenkins.getInstance().save()

return "Kubernetes cloud {{name}} created successfully"
'''
    try:
        result = _run_groovy(jk, script)
        return {"status": "success", "message": result}
    except Exception as e:
        raise JenkinsException(f'Failed to create Kubernetes cloud: {e}')


@write_only
async def add_pod_template(jk, cloud_name: str, template_config: dict) -> dict:
    """添加Pod模板到Kubernetes云
    
    参数:
        cloud_name: 云名称
        template_config: 模板配置 {
            name: str,
            label: str,
            image: str,
            yaml: str (optional),
            num_executors: int,
            instance_cap: int,
            remote_fs: str
        }
    
    返回:
        添加结果
    """
    
    name = template_config.get('name', '')
    label = template_config.get('label', '')
    image = template_config.get('image', 'jenkins/inbound-agent')
    yaml = template_config.get('yaml', '')
    num_executors = template_config.get('num_executors', 1)
    instance_cap = template_config.get('instance_cap', 0)
    remote_fs = template_config.get('remote_fs', '/home/jenkins')
    
    script = f'''
import org.csanchez.jenkins.plugins.kubernetes.KubernetesCloud
import org.csanchez.jenkins.plugins.kubernetes.PodTemplate
import jenkins.model.Jenkins
import hudson.model.Label
import hudson.slaves.Cloud
import hudson.slaves.JNLPLauncher

def cloud = Jenkins.getInstance().clouds.find {{ it.name == "{cloud_name}" }}
if (!cloud) {{
    return "Cloud {{cloud_name}} not found"
}}

def existing = cloud.templates.find {{ it.name == "{name}" }}
if (existing) {{
    return "Template {{name}} already exists"
}}

def template = new PodTemplate()
template.name = "{name}"
template.label = "{label}"
template.image = "{image}"
template.instanceCap = {instance_cap}
template.remoteFs = "{remote_fs}"

{(f'template.yaml = """{yaml}"""' if yaml else '')}

cloud.templates.add(template)
Jenkins.getInstance().save()

return "Template {{name}} added to cloud {{cloud_name}}"
'''
    try:
        result = _run_groovy(jk, script)
        return {"status": "success", "message": result}
    except Exception as e:
        raise JenkinsException(f'Failed to add template: {e}')


@write_only
async def get_kubernetes_pods(jk, namespace: str = None) -> dict:
    """获取Kubernetes pods信息
    
    参数:
        namespace: 可选的命名空间
    
    返回:
        Pods信息
    """
    
    script = f'''
import org.csanchez.jenkins.plugins.kubernetes.KubernetesCloud
import jenkins.model.Jenkins
import groovy.json.JsonOutput

def result = [
    clouds: [],
    pods: []
]

Jenkins.getInstance().clouds.each {{ cloud ->
    if (cloud.class.name == 'org.csanchez.jenkins.plugins.kubernetes.KubernetesCloud') {{
        def cloudInfo = [
            name: cloud.name,
            namespace: cloud.namespace ?: 'default',
            serverUrl: cloud.serverUrl,
            templates: cloud.templates.collect {{ t -> [name: t.name, label: t.label ?: '', image: t.image ?: ''] }}
        ]
        result.clouds << cloudInfo
    }}
}}

return JsonOutput.toJson(result)
'''
    try:
        result = _run_groovy(jk, script)
        import json
        return json.loads(result)
    except Exception as e:
        raise JenkinsException(f'Failed to get pods: {e}')


@write_only
async def get_clouds_by_type(jk) -> list:
    """获取所有云并按类型归类

    返回各类云的类型标识，便于路由到对应的插件管理工具:
      - docker: 使用 docker_cloud 模块管理
      - kubernetes: 使用 kubernetes_cloud 模块管理
      - yad: 使用 yad_cloud 模块管理
      - other: 其他云类型
    """
    script = '''
import jenkins.model.Jenkins
import groovy.json.JsonOutput

def result = []
Jenkins.getInstance().clouds.each { cloud ->
    def entry = [
        name: cloud.name,
        type: "other",
        pluginModule: "",
        className: cloud.class.name
    ]

    if (cloud.class.name == "com.nirima.jenkins.plugins.docker.DockerCloud") {
        entry.type = "docker"
        entry.pluginModule = "docker_cloud"
    } else if (cloud.class.name == "org.csanchez.jenkins.plugins.kubernetes.KubernetesCloud") {
        entry.type = "kubernetes"
        entry.pluginModule = "kubernetes_cloud"
    } else if (cloud.class.name == "com.github.kostyasha.yad.DockerCloud") {
        entry.type = "yad"
        entry.pluginModule = "yad_cloud"
    }

    entry.templateCount = cloud.templates?.size() ?: 0
    result << entry
}
return JsonOutput.toJson(result)
'''
    try:
        result = _run_groovy(jk, script)
        import json
        return json.loads(result)
    except Exception as e:
        raise JenkinsException(f'Failed to get clouds by type: {e}')