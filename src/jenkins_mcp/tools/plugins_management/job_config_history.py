"""
Job Config History Plugin管理模块

支持对Jenkins job-config-history-plugin的管理:
- 查看全局配置历史
- 查看指定job的配置历史
- 查看指定node的配置历史
- 获取某个历史版本的配置文件内容
- 两个历史版本的内容对比
- 回退job配置到指定历史版本
- 回退node配置到指定历史版本
- 删除job的某个历史版本
- 删除node的某个历史版本
- 恢复已删除的job
"""

import difflib
import json
import urllib.parse
from typing import Optional

import requests
from jenkins_mcp.jenkins import Jenkins


async def get_all_config_history(jk: Jenkins, filter: str = 'all') -> list:
    """获取全局配置历史

    通过REST API获取所有配置修改历史记录

    参数:
        filter: 过滤条件，可选值: all, system, jobs, deleted
    """
    try:
        response = jk.jenkins_open(
            requests.Request('GET', jk._build_url(f'jobConfigHistory/api/json?filter={filter}'))
        )
        data = json.loads(response)
        return data.get('configs', [])
    except Exception:
        script = '''
import groovy.json.JsonOutput
import hudson.plugins.jobConfigHistory.PluginUtils
import hudson.plugins.jobConfigHistory.ConfigInfoCollector

def dao = PluginUtils.getHistoryDao()
def plugin = PluginUtils.getPlugin()
def collector = new ConfigInfoCollector(dao, plugin.getMaxEntriesPerPage())
def configs = collector.getJobConfigs("all", 0, -1)
def result = configs.collect { c ->
    [
        user: c.user,
        userID: c.userID,
        date: c.date,
        configExists: c.configExists,
        job: c.job,
        operation: c.operation,
        currentName: c.currentName,
        oldName: c.oldName,
        changeReasonComment: c.changeReasonComment
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


async def get_job_config_history(jk: Jenkins, job_name: str) -> list:
    """获取指定job的配置历史

    通过REST API获取某个job的配置修改记录
    """
    try:
        folder_url, short_name = jk._get_job_folder(job_name)
        url = jk._build_url(f'{folder_url}job/{short_name}/jobConfigHistory/api/json')
        response = jk.jenkins_open(requests.Request('GET', url))
        data = json.loads(response)
        return data.get('jobConfigHistory', data)
    except Exception:
        script = f'''
import groovy.json.JsonOutput
import jenkins.model.Jenkins
import hudson.plugins.jobConfigHistory.PluginUtils

def jenkins = Jenkins.get()
def job = jenkins.getItemByFullName("{job_name}")
if (job == null) return "[]"
def result = []
def dao = PluginUtils.getHistoryDao()
def configFile = job.getConfigFile()
def revisions = dao.getRevisions(configFile)
revisions.each {{ timestamp, descr ->
    result.add([
        timestamp: timestamp,
        user: descr.user,
        userID: descr.userId,
        operation: descr.operation,
        currentName: descr.currentName,
        oldName: descr.oldName,
        changeReasonComment: descr.changeReasonComment
    ])
}}
result = result.reverse()
return JsonOutput.toJson(result)
'''
        result = jk.run_script(script)
        if result:
            try:
                return json.loads(result)
            except:
                return [{'error': 'Failed to parse result', 'raw': result}]
        return []


async def get_node_config_history(jk: Jenkins, node_name: str) -> list:
    """获取指定node的配置历史

    通过REST API获取某个node的配置修改记录
    """
    try:
        url = jk._build_url(f'computer/{node_name}/jobConfigHistory/api/json')
        response = jk.jenkins_open(requests.Request('GET', url))
        data = json.loads(response)
        return data.get('jobConfigHistory', data)
    except Exception:
        script = f'''
import groovy.json.JsonOutput
import jenkins.model.Jenkins
import hudson.plugins.jobConfigHistory.PluginUtils

def jenkins = Jenkins.get()
def node = jenkins.getNode("{node_name}")
if (node == null) return "[]"
def result = []
def dao = PluginUtils.getHistoryDao()
def revisions = dao.getRevisions(node)
revisions.each {{ timestamp, descr ->
    result.add([
        timestamp: timestamp,
        user: descr.user,
        userID: descr.userId,
        operation: descr.operation,
        currentName: descr.currentName,
        oldName: descr.oldName,
        changeReasonComment: descr.changeReasonComment
    ])
}}
result = result.reverse()
return JsonOutput.toJson(result)
'''
        result = jk.run_script(script)
        if result:
            try:
                return json.loads(result)
            except:
                return [{'error': 'Failed to parse result', 'raw': result}]
        return []


async def get_config_file_content(jk: Jenkins, job_name: str, timestamp: str) -> Optional[dict]:
    """获取某个历史版本的配置文件内容"""
    script = f'''
import groovy.json.JsonOutput
import jenkins.model.Jenkins
import hudson.plugins.jobConfigHistory.PluginUtils

def jenkins = Jenkins.get()
def job = jenkins.getItemByFullName("{job_name}")
if (job == null) return JsonOutput.toJson([success: false, error: "Job not found: {job_name}"])

try {{
    def dao = PluginUtils.getHistoryDao()
    def configFile = job.getConfigFile()
    def oldRevision = dao.getOldRevision(configFile, "{timestamp}")
    if (oldRevision == null) {{
        return JsonOutput.toJson([success: false, error: "Revision not found: {timestamp}"])
    }}
    def content = oldRevision.getFile().getText("UTF-8")
    return JsonOutput.toJson([success: true, content: content, job: "{job_name}", timestamp: "{timestamp}"])
}} catch (Exception e) {{
    return JsonOutput.toJson([success: false, error: e.getMessage()])
}}
'''
    result = jk.run_script(script)
    if result:
        try:
            return json.loads(result)
        except:
            return {'error': 'Failed to parse result', 'raw': result}
    return None


async def restore_job_config(jk: Jenkins, job_name: str, timestamp: str) -> dict:
    """回退job配置到指定历史版本"""
    script = f'''
import groovy.json.JsonOutput
import jenkins.model.Jenkins
import hudson.plugins.jobConfigHistory.PluginUtils

def jenkins = Jenkins.get()
def job = jenkins.getItemByFullName("{job_name}")
if (job == null) return JsonOutput.toJson([success: false, error: "Job not found: {job_name}"])

try {{
    def dao = PluginUtils.getHistoryDao()
    dao.copyHistoryAndDelete(job, "{timestamp}")
    return JsonOutput.toJson([success: true, job: "{job_name}", timestamp: "{timestamp}"])
}} catch (Exception e) {{
    return JsonOutput.toJson([success: false, error: e.getMessage()])
}}
'''
    result = jk.run_script(script)
    try:
        return json.loads(result)
    except:
        return {'success': True, 'job': job_name, 'timestamp': timestamp, 'raw': result}


async def restore_node_config(jk: Jenkins, node_name: str, timestamp: str) -> dict:
    """回退node配置到指定历史版本"""
    script = f'''
import groovy.json.JsonOutput
import jenkins.model.Jenkins
import hudson.plugins.jobConfigHistory.PluginUtils

def jenkins = Jenkins.get()
def node = jenkins.getNode("{node_name}")
if (node == null) return JsonOutput.toJson([success: false, error: "Node not found: {node_name}"])

try {{
    def dao = PluginUtils.getHistoryDao()
    dao.copyHistoryAndDelete(node, "{timestamp}")
    return JsonOutput.toJson([success: true, node: "{node_name}", timestamp: "{timestamp}"])
}} catch (Exception e) {{
    return JsonOutput.toJson([success: false, error: e.getMessage()])
}}
'''
    result = jk.run_script(script)
    try:
        return json.loads(result)
    except:
        return {'success': True, 'node': node_name, 'timestamp': timestamp, 'raw': result}


async def delete_job_config_revision(jk: Jenkins, job_name: str, timestamp: str) -> dict:
    """删除job的某个历史版本"""
    script = f'''
import groovy.json.JsonOutput
import jenkins.model.Jenkins
import hudson.plugins.jobConfigHistory.PluginUtils

def jenkins = Jenkins.get()
def job = jenkins.getItemByFullName("{job_name}")
if (job == null) return JsonOutput.toJson([success: false, error: "Job not found: {job_name}"])

try {{
    def dao = PluginUtils.getHistoryDao()
    dao.deleteRevision(job, "{timestamp}")
    return JsonOutput.toJson([success: true, job: "{job_name}", timestamp: "{timestamp}"])
}} catch (Exception e) {{
    return JsonOutput.toJson([success: false, error: e.getMessage()])
}}
'''
    result = jk.run_script(script)
    try:
        return json.loads(result)
    except:
        return {'success': True, 'job': job_name, 'timestamp': timestamp, 'raw': result}


async def delete_node_config_revision(jk: Jenkins, node_name: str, timestamp: str) -> dict:
    """删除node的某个历史版本"""
    script = f'''
import groovy.json.JsonOutput
import jenkins.model.Jenkins
import hudson.plugins.jobConfigHistory.PluginUtils

def jenkins = Jenkins.get()
def node = jenkins.getNode("{node_name}")
if (node == null) return JsonOutput.toJson([success: false, error: "Node not found: {node_name}"])

try {{
    def dao = PluginUtils.getHistoryDao()
    dao.deleteRevision(node, "{timestamp}")
    return JsonOutput.toJson([success: true, node: "{node_name}", timestamp: "{timestamp}"])
}} catch (Exception e) {{
    return JsonOutput.toJson([success: false, error: e.getMessage()])
}}
'''
    result = jk.run_script(script)
    try:
        return json.loads(result)
    except:
        return {'success': True, 'node': node_name, 'timestamp': timestamp, 'raw': result}


async def restore_deleted_job(jk: Jenkins, job_name: str) -> dict:
    """恢复已删除的job"""
    script = f'''
import groovy.json.JsonOutput
import hudson.plugins.jobConfigHistory.PluginUtils

def dao = PluginUtils.getHistoryDao()
def deletedJobs = dao.getDeletedJobs()
def deletedDir = deletedJobs.find {{ d -> d.getName().startsWith("{job_name}") }}
if (deletedDir == null) return JsonOutput.toJson([success: false, error: "Deleted job not found: {job_name}"])

try {{
    def timestampDirs = deletedDir.listFiles().findAll {{ f ->
        f.isDirectory() && new java.io.File(f, "config.xml").exists()
    }}
    if (timestampDirs.isEmpty()) return JsonOutput.toJson([success: false, error: "No revision found for deleted job"])
    timestampDirs.sort()
    def lastTimestamp = timestampDirs[-1].getName()
    dao.copyHistoryAndDelete("{job_name}", lastTimestamp)
    return JsonOutput.toJson([success: true, job: "{job_name}", timestamp: lastTimestamp])
}} catch (Exception e) {{
    return JsonOutput.toJson([success: false, error: e.getMessage()])
}}
'''
    result = jk.run_script(script)
    try:
        return json.loads(result)
    except:
        return {'success': True, 'job': job_name, 'raw': result}


async def get_config_diff(jk: Jenkins, job_name: str, timestamp1: str, timestamp2: str) -> dict:
    """获取两个历史版本的配置差异

    使用Python的difflib计算unified diff
    """
    content1_result = await get_config_file_content(jk, job_name, timestamp1)
    content2_result = await get_config_file_content(jk, job_name, timestamp2)

    if not content1_result or not content1_result.get('success'):
        return {'success': False, 'error': f'Failed to get revision {timestamp1}: {content1_result}'}
    if not content2_result or not content2_result.get('success'):
        return {'success': False, 'error': f'Failed to get revision {timestamp2}: {content2_result}'}

    content1 = content1_result.get('content', '')
    content2 = content2_result.get('content', '')

    lines1 = content1.splitlines(keepends=True)
    lines2 = content2.splitlines(keepends=True)

    diff = list(difflib.unified_diff(
        lines1, lines2,
        fromfile=f'{job_name}@{timestamp1}',
        tofile=f'{job_name}@{timestamp2}',
        lineterm=''
    ))

    stats = {'added': 0, 'removed': 0, 'changed': 0}
    for line in diff:
        if line.startswith('+') and not line.startswith('+++'):
            stats['added'] += 1
        elif line.startswith('-') and not line.startswith('---'):
            stats['removed'] += 1
    stats['changed'] = min(stats['added'], stats['removed'])

    return {
        'success': True,
        'job': job_name,
        'timestamp1': timestamp1,
        'timestamp2': timestamp2,
        'diff': diff,
        'stats': stats
    }
