"""
Downstream Build View Plugin管理模块

支持对Jenkins downstream-buildview-plugin的管理:
- 查看job配置的下游任务列表
- 查看job配置的上游任务列表
- 查看某次构建触发的下游构建
- 查看某次构建的上游触发信息
- 递归获取完整下游链路树
- 递归获取完整上游链路链
"""

import json
from typing import Optional

from jenkins_mcp.jenkins import Jenkins, JenkinsException


def _run_groovy(jk, script: str) -> str:
    return jk.run_script(script)


def _escape(s: str) -> str:
    return s.replace('\\', '\\\\').replace('"', '\\"')


async def get_job_downstream_projects(jk: Jenkins, job_name: str) -> list:
    """获取job配置的下游任务列表"""
    job = _escape(job_name)
    script = '''
import hudson.model.AbstractProject
import jenkins.model.Jenkins
import groovy.json.JsonOutput

def job = Jenkins.get().getItemByFullName("JOB_NAME")
if (job == null) return "[]"
if (!(job instanceof AbstractProject)) return JsonOutput.toJson([error: "Not a freestyle project"])

def result = job.getDownstreamProjects().collect { p ->
    [
        name: p.fullName,
        url: p.url,
        displayName: p.displayName,
        lastBuild: p.lastBuild?.number ?: 0,
        lastCompletedBuild: p.lastCompletedBuild?.number ?: 0,
        lastSuccessfulBuild: p.lastSuccessfulBuild?.number ?: 0,
        lastFailedBuild: p.lastFailedBuild?.number ?: 0,
        health: p.buildHealthReport?.score ?: 0
    ]
}
return JsonOutput.toJson(result)
'''.replace('JOB_NAME', job)
    try:
        result = _run_groovy(jk, script)
        return json.loads(result)
    except Exception as e:
        raise JenkinsException(f'Failed to get downstream projects: {e}')


async def get_job_upstream_projects(jk: Jenkins, job_name: str) -> list:
    """获取job配置的上游任务列表"""
    job = _escape(job_name)
    script = '''
import hudson.model.AbstractProject
import jenkins.model.Jenkins
import groovy.json.JsonOutput

def job = Jenkins.get().getItemByFullName("JOB_NAME")
if (job == null) return "[]"
if (!(job instanceof AbstractProject)) return JsonOutput.toJson([error: "Not a freestyle project"])

def result = job.getUpstreamProjects().collect { p ->
    [
        name: p.fullName,
        url: p.url,
        displayName: p.displayName,
        lastBuild: p.lastBuild?.number ?: 0,
        lastCompletedBuild: p.lastCompletedBuild?.number ?: 0,
        lastSuccessfulBuild: p.lastSuccessfulBuild?.number ?: 0,
        lastFailedBuild: p.lastFailedBuild?.number ?: 0,
        health: p.buildHealthReport?.score ?: 0
    ]
}
return JsonOutput.toJson(result)
'''.replace('JOB_NAME', job)
    try:
        result = _run_groovy(jk, script)
        return json.loads(result)
    except Exception as e:
        raise JenkinsException(f'Failed to get upstream projects: {e}')


async def get_build_downstream(jk: Jenkins, job_name: str, build_number: int) -> list:
    """获取某次构建触发的下游构建列表"""
    job = _escape(job_name)
    script = '''
import hudson.model.AbstractBuild
import hudson.model.AbstractProject
import jenkins.model.Jenkins
import org.jvnet.hudson.plugins.DownstreamBuildViewAction
import groovy.json.JsonOutput

def job = Jenkins.get().getItemByFullName("JOB_NAME")
if (job == null) return "[]"
def build = (job instanceof AbstractProject) ? job.getBuildByNumber(BUILD_NUM) : null
if (build == null) return "[]"

def action = build.getAction(DownstreamBuildViewAction.class)
if (action == null) return "[]"

def field = DownstreamBuildViewAction.class.getDeclaredField("downstreamBuilds")
field.setAccessible(true)
def downstreamMap = field.get(action) as Map<String, Integer>

def result = []
downstreamMap.each { projName, buildNum ->
    def downProject = Jenkins.get().getItemByFullName(projName)
    def downBuild = (downProject instanceof AbstractProject) ? downProject.getBuildByNumber(buildNum) : null
    result << [
        projectName: projName,
        buildNumber: buildNum,
        result: downBuild?.result?.toString() ?: '',
        duration: downBuild?.duration ?: 0,
        timestamp: downBuild?.timestamp?.timeInMillis ?: 0,
        url: downBuild?.url ?: '',
        displayName: downBuild?.displayName ?: '',
        built: buildNum > 0
    ]
}
return JsonOutput.toJson(result)
'''.replace('JOB_NAME', job).replace('BUILD_NUM', str(build_number))
    try:
        result = _run_groovy(jk, script)
        return json.loads(result)
    except Exception as e:
        raise JenkinsException(f'Failed to get build downstream: {e}')


async def get_build_upstream(jk: Jenkins, job_name: str, build_number: int) -> Optional[dict]:
    """获取某次构建的上游触发信息"""
    job = _escape(job_name)
    script = '''
import hudson.model.Cause
import hudson.model.AbstractBuild
import hudson.model.AbstractProject
import jenkins.model.Jenkins
import groovy.json.JsonOutput

def job = Jenkins.get().getItemByFullName("JOB_NAME")
if (job == null) return "null"
def build = (job instanceof AbstractProject) ? job.getBuildByNumber(BUILD_NUM) : null
if (build == null) return "null"

def causes = build.getCauses(Cause.UpstreamCause.class)
def result = []
causes.each { cause ->
    def upProject = Jenkins.get().getItemByFullName(cause.upstreamProject)
    def upBuild = (upProject instanceof AbstractProject) ? upProject.getBuildByNumber(cause.upstreamBuild) : null
    result << [
        upstreamProject: cause.upstreamProject,
        upstreamBuild: cause.upstreamBuild,
        upstreamUrl: cause.upstreamUrl ?: '',
        displayName: cause.toString(),
        result: upBuild?.result?.toString() ?: '',
        duration: upBuild?.duration ?: 0,
        timestamp: upBuild?.timestamp?.timeInMillis ?: 0
    ]
}
return JsonOutput.toJson(result)
'''.replace('JOB_NAME', job).replace('BUILD_NUM', str(build_number))
    try:
        result = _run_groovy(jk, script)
        return json.loads(result)
    except Exception as e:
        raise JenkinsException(f'Failed to get build upstream: {e}')



async def get_build_downstream_tree(jk: Jenkins, job_name: str, build_number: int, max_depth: int = 5) -> Optional[dict]:
    """递归获取完整下游构建链路树"""
    job = _escape(job_name)
    script = '''
import hudson.model.AbstractBuild
import hudson.model.AbstractProject
import hudson.model.Cause
import jenkins.model.Jenkins
import org.jvnet.hudson.plugins.DownstreamBuildViewAction
import groovy.json.JsonOutput

def job = Jenkins.get().getItemByFullName("JOB_NAME")
if (job == null) return "null"
def build = (job instanceof AbstractProject) ? job.getBuildByNumber(BUILD_NUM) : null
if (build == null) return "null"

def maxDepth = MAX_DEPTH
def field
try {
    field = DownstreamBuildViewAction.class.getDeclaredField("downstreamBuilds")
    field.setAccessible(true)
} catch (Exception e) {
    return JsonOutput.toJson([error: "Cannot access DownstreamBuildViewAction"])
}

def buildNode(AbstractBuild b, int depth) {
    if (b == null) return null
    if (depth > maxDepth) return [name: b.fullDisplayName, number: b.number, truncated: true]

    def node = [
        jobName: b.parent.fullName,
        buildNumber: b.number,
        result: b.result?.toString() ?: '',
        duration: b.duration,
        timestamp: b.timestamp?.timeInMillis ?: 0,
        url: b.url,
        displayName: b.displayName,
        depth: depth,
        downstreams: []
    ]

    def action = b.getAction(DownstreamBuildViewAction.class)
    if (action != null) {
        def downstreamMap = field.get(action) as Map<String, Integer>
        downstreamMap.each { projName, buildNum ->
            def downProject = Jenkins.get().getItemByFullName(projName)
            def downBuild = (downProject instanceof AbstractProject) ? downProject.getBuildByNumber(buildNum) : null
            def child = buildNode(downBuild, depth + 1)
            if (child != null) {
                node.downstreams << child
            } else if (buildNum > 0) {
                node.downstreams << [jobName: projName, buildNumber: buildNum, result: '', built: true, unreachable: true]
            }
        }
    }

    if (b.parent instanceof AbstractProject) {
        b.parent.getDownstreamProjects().each { downProject ->
            def already = node.downstreams.any { it.jobName == downProject.fullName }
            if (!already) {
                node.downstreams << [
                    jobName: downProject.fullName,
                    buildNumber: 0,
                    result: '',
                    built: false,
                    depth: depth + 1
                ]
            }
        }
    }

    return node
}

def root = buildNode(build, 0)
return JsonOutput.toJson(root)
'''.replace('JOB_NAME', job).replace('BUILD_NUM', str(build_number)).replace('MAX_DEPTH', str(max_depth))
    try:
        result = _run_groovy(jk, script)
        return json.loads(result) if result else None
    except Exception as e:
        raise JenkinsException(f'Failed to get downstream tree: {e}')


async def get_build_upstream_chain(jk: Jenkins, job_name: str, build_number: int, max_depth: int = 10) -> Optional[dict]:
    """递归获取完整上游触发链"""
    job = _escape(job_name)
    script = '''
import hudson.model.AbstractBuild
import hudson.model.AbstractProject
import hudson.model.Cause
import jenkins.model.Jenkins
import groovy.json.JsonOutput

def job = Jenkins.get().getItemByFullName("JOB_NAME")
if (job == null) return "null"
def build = (job instanceof AbstractProject) ? job.getBuildByNumber(BUILD_NUM) : null
if (build == null) return "null"

def maxDepth = MAX_DEPTH

def buildUpstreamNode(AbstractBuild b, int depth) {
    if (b == null) return null
    if (depth > maxDepth) return [name: b.fullDisplayName, number: b.number, truncated: true]

    def node = [
        jobName: b.parent.fullName,
        buildNumber: b.number,
        result: b.result?.toString() ?: '',
        duration: b.duration,
        timestamp: b.timestamp?.timeInMillis ?: 0,
        url: b.url,
        displayName: b.displayName,
        depth: depth,
        upstreams: []
    ]

    def causes = b.getCauses(Cause.UpstreamCause.class)
    causes.each { cause ->
        def upProject = Jenkins.get().getItemByFullName(cause.upstreamProject)
        def upBuild = (upProject instanceof AbstractProject) ? upProject.getBuildByNumber(cause.upstreamBuild) : null
        def parent = buildUpstreamNode(upBuild, depth + 1)
        if (parent != null) {
            node.upstreams << parent
        } else {
            node.upstreams << [
                jobName: cause.upstreamProject,
                buildNumber: cause.upstreamBuild,
                result: '',
                displayName: cause.toString(),
                depth: depth + 1
            ]
        }
    }

    return node
}

def root = buildUpstreamNode(build, 0)
return JsonOutput.toJson(root)
'''.replace('JOB_NAME', job).replace('BUILD_NUM', str(build_number)).replace('MAX_DEPTH', str(max_depth))
    try:
        result = _run_groovy(jk, script)
        return json.loads(result) if result else None
    except Exception as e:
        raise JenkinsException(f'Failed to get upstream chain: {e}')
