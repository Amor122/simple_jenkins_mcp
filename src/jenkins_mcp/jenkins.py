#!/usr/bin/env python
"""
Jenkins MCP Server - 基于python-jenkins的实现
优先级: Jenkins源码 > python-jenkins > 其他参考资料
"""

import os
import json
import re
import socket
import urllib.parse
from typing import Any, Optional
from functools import wraps

import requests
from requests.auth import HTTPBasicAuth
from requests.adapters import HTTPAdapter
from urllib3.util import parse_url, Retry
from urllib3.exceptions import InsecureRequestWarning
from http.client import BadStatusLine
import xml.etree.ElementTree as ET

# REST Endpoints - 直接从python-jenkins提取
INFO = 'api/json'
PLUGIN_INFO = '/pluginManager/api/json?depth=%(depth)s'
CRUMB_URL = 'crumbIssuer/api/json'
WHOAMI_URL = 'me/api/json?depth=%(depth)s'
JOBS_QUERY = '?tree=%s'
JOBS_QUERY_TREE = 'jobs[url,color,name,%s]'
JOB_INFO = '%(folder_url)sjob/%(short_name)s/api/json?depth=%(depth)s'
JOB_NAME = '%(folder_url)sjob/%(short_name)s/api/json?tree=name'
ALL_BUILDS = '%(folder_url)sjob/%(short_name)s/api/json?tree=allBuilds[number,url]'
Q_INFO = 'queue/api/json?depth=0'
Q_ITEM = 'queue/item/%(number)d/api/json?depth=%(depth)s'
CANCEL_QUEUE = 'queue/cancelItem?id=%(id)s'
CREATE_JOB = '%(folder_url)screateItem?name=%(short_name)s'
CONFIG_JOB = '%(folder_url)sjob/%(short_name)s/config.xml'
DELETE_JOB = '%(folder_url)sjob/%(short_name)s/doDelete'
ENABLE_JOB = '%(folder_url)sjob/%(short_name)s/enable'
DISABLE_JOB = '%(folder_url)sjob/%(short_name)s/disable'
SET_JOB_BUILD_NUMBER = '%(folder_url)sjob/%(short_name)s/nextbuildnumber/submit'
COPY_JOB = '%(from_folder_url)screateItem?name=%(to_short_name)s&mode=copy&from=%(from_short_name)s'
RENAME_JOB = '%(from_folder_url)sjob/%(from_short_name)s/doRename?newName=%(to_short_name)s'
BUILD_JOB = '%(folder_url)sjob/%(short_name)s/build'
STOP_BUILD = '%(folder_url)sjob/%(short_name)s/%(number)s/stop'
BUILD_WITH_PARAMS_JOB = '%(folder_url)sjob/%(short_name)s/buildWithParameters'
BUILD_INFO = '%(folder_url)sjob/%(short_name)s/%(number)s/api/json?depth=%(depth)s'
BUILD_CONSOLE_OUTPUT = '%(folder_url)sjob/%(short_name)s/%(number)s/consoleText'
BUILD_ENV_VARS = '%(folder_url)sjob/%(short_name)s/%(number)s/injectedEnvVars/api/json?depth=%(depth)s'
BUILD_TEST_REPORT = '%(folder_url)sjob/%(short_name)s/%(number)s/testReport/api/json?depth=%(depth)s'
BUILD_ARTIFACT = '%(folder_url)sjob/%(short_name)s/%(number)s/artifact/%(artifact)s'
BUILD_STAGES = '%(folder_url)sjob/%(short_name)s/%(number)s/wfapi/describe/'
DELETE_BUILD = '%(folder_url)sjob/%(short_name)s/%(number)s/doDelete'
WIPEOUT_JOB_WORKSPACE = '%(folder_url)sjob/%(short_name)s/doWipeOutWorkspace'
NODE_LIST = 'computer/api/json?depth=%(depth)s'
CREATE_NODE = 'computer/doCreateItem'
DELETE_NODE = 'computer/%(name)s/doDelete'
NODE_INFO = 'computer/%(name)s/api/json?depth=%(depth)s'
NODE_TYPE = 'hudson.slaves.DumbSlave$DescriptorImpl'
TOGGLE_OFFLINE = 'computer/%(name)s/toggleOffline?offlineMessage=%(msg)s'
CONFIG_NODE = 'computer/%(name)s/config.xml'
VIEW_NAME = '%(folder_url)sview/%(short_name)s/api/json?tree=name'
VIEW_JOBS = 'view/%(name)s/api/json?tree=jobs[url,color,name]'
CREATE_VIEW = '%(folder_url)screateView?name=%(short_name)s'
CONFIG_VIEW = '%(folder_url)sview/%(short_name)s/config.xml'
DELETE_VIEW = '%(folder_url)sview/%(short_name)s/doDelete'
SCRIPT_TEXT = 'scriptText'
NODE_SCRIPT_TEXT = 'computer/%(node)s/scriptText'
PROMOTION_NAME = '%(folder_url)sjob/%(short_name)s/promotion/process/%(name)s/api/json?tree=name'
PROMOTION_INFO = '%(folder_url)sjob/%(short_name)s/promotion/api/json?depth=%(depth)s'
DELETE_PROMOTION = '%(folder_url)sjob/%(short_name)s/promotion/process/%(name)s/doDelete'
CREATE_PROMOTION = '%(folder_url)sjob/%(short_name)s/promotion/createProcess?name=%(name)s'
CONFIG_PROMOTION = '%(folder_url)sjob/%(short_name)s/promotion/process/%(name)s/config.xml'
LIST_CREDENTIALS = '%(folder_url)sjob/%(short_name)s/credentials/store/folder/domain/%(domain_name)s/api/json?tree=credentials[id]'
CREATE_CREDENTIAL = '%(folder_url)sjob/%(short_name)s/credentials/store/folder/domain/%(domain_name)s/createCredentials'
CONFIG_CREDENTIAL = '%(folder_url)sjob/%(short_name)s/credentials/store/folder/domain/%(domain_name)s/credential/%(name)s/config.xml'
CREDENTIAL_INFO = '%(folder_url)sjob/%(short_name)s/credentials/store/folder/domain/%(domain_name)s/credential/%(name)s/api/json?depth=0'
QUIET_DOWN = 'quietDown'
CANCEL_QUIET_DOWN = 'cancelQuietDown'
SAFE_RESTART = 'safeRestart'
RESTART = 'restart'
RELOAD = 'reload'
PLUGIN_INSTALL = '/pluginManager/installNecessaryPlugins'
PLUGIN_UNINSTALL = '/plugin/%(short_name)s/doUninstall'

LAUNCHER_SSH = 'hudson.plugins.sshslaves.SSHLauncher'
LAUNCHER_COMMAND = 'hudson.slaves.CommandLauncher'
LAUNCHER_JNLP = 'hudson.slaves.JNLPLauncher'
LAUNCHER_WINDOWS_SERVICE = 'hudson.os.windows.ManagedWindowsServiceLauncher'
DEFAULT_HEADERS = {'Content-Type': 'text/xml; charset=utf-8'}


# 异常定义 - 直接从python-jenkins提取
class JenkinsException(Exception):
    """General exception type for jenkins-API-related failures."""
    pass


class NotFoundException(JenkinsException):
    """A special exception to call out the case of receiving a 404."""
    pass


class EmptyResponseException(JenkinsException):
    """A special exception to call out the case receiving an empty response."""
    pass


class BadHTTPException(JenkinsException):
    """A special exception to call out the case of a broken HTTP response."""
    pass


class TimeoutException(JenkinsException):
    """A special exception to call out in the case of a socket timeout."""
    pass


class Jenkins:
    """
    Jenkins REST API封装类
    
    基于python-jenkins的实现，优先级：
    1. Jenkins源码
    2. python-jenkins库
    3. 其他参考资料
    """

    def __init__(
            self,
            url: str,
            username: Optional[str] = None,
            password: Optional[str] = None,
            timeout: int = 30,
            verify_ssl: bool = True,
    ):
        self.server = url.rstrip('/') + '/'
        self.timeout = timeout
        self.crumb = None
        self._verify_ssl = verify_ssl

        self._session = requests.Session()
        if username and password:
            self._session.auth = HTTPBasicAuth(username, password)

        if not verify_ssl:
            import warnings
            warnings.filterwarnings('ignore', category=InsecureRequestWarning)
            self._session.verify = False

        self._session.mount(
            self.server,
            HTTPAdapter(max_retries=Retry(total=0, backoff_factor=0.1))
        )

    def _build_url(self, format_spec: str, variables: Optional[dict] = None) -> str:
        """构建完整的URL"""
        if variables:
            url_path = format_spec % self._get_encoded_params(variables)
        else:
            url_path = format_spec
        return str(urllib.parse.urljoin(self.server, url_path))

    def _get_encoded_params(self, params: dict) -> dict:
        """URL编码参数"""
        for k, v in params.items():
            if k in ["name", "msg", "short_name", "from_short_name",
                     "to_short_name", "folder_url", "from_folder_url", "to_folder_url",
                     "artifact", "number", "node", "id", "domain_name"]:
                params[k] = urllib.parse.quote(str(v).encode('utf8'))
        return params

    def _get_job_folder(self, name: str) -> tuple:
        """
        解析job名称，返回folder路径和短名称
        
        支持CloudBees Folder插件的路径格式
        """
        a_path = name.split('/')
        short_name = a_path[-1]
        folder_url = ('job/' + '/job/'.join(a_path[:-1]) + '/') if len(a_path) > 1 else ''
        return folder_url, short_name

    def _maybe_add_auth(self):
        """确保认证已配置"""
        pass  # 已在初始化时设置

    def maybe_add_crumb(self, req) -> None:
        """自动添加CSRF crumb"""
        if self.crumb is None:
            try:
                response = self.jenkins_open(
                    requests.Request('GET', self._build_url(CRUMB_URL)),
                    add_crumb=False
                )
                if response:
                    self.crumb = json.loads(response)
                else:
                    self.crumb = False
            except (NotFoundException, EmptyResponseException):
                self.crumb = False
            except Exception:
                self.crumb = False

        if self.crumb:
            req.headers[self.crumb['crumbRequestField']] = self.crumb['crumb']

    def jenkins_open(
            self,
            req,
            add_crumb: bool = True,
            resolve_auth: bool = True
    ) -> str:
        """发送请求并返回响应文本"""
        return self.jenkins_request(req, add_crumb, resolve_auth).text

    def jenkins_request(
            self,
            req,
            add_crumb: bool = True,
            resolve_auth: bool = True,
            stream: bool = False
    ):
        """发送HTTP请求"""
        try:
            if resolve_auth:
                self._maybe_add_auth()
            if add_crumb:
                self.maybe_add_crumb(req)

            prepared = self._session.prepare_request(req)

            settings = self._session.merge_environment_settings(
                prepared.url, {}, stream, self._session.verify, None
            )
            response = self._session.send(prepared, **settings)

            # 403自动重试机制
            if add_crumb and response.status_code == 403 and self.crumb:
                self.crumb = None
                self.maybe_add_crumb(req)
                prepared = self._session.prepare_request(req)
                response = self._session.send(prepared, **settings)
            
            response.raise_for_status()
            return response
        
        except requests.exceptions.HTTPError as e:
            if e.response and e.response.status_code in [401, 403, 500]:
                msg = f'Error in request. Possibly authentication failed [{e.response.status_code}]: {e.response.reason}'
                if e.response.text:
                    msg += '\n' + e.response.text
                raise JenkinsException(msg)
            elif e.response and e.response.status_code == 404:
                raise NotFoundException('Requested item could not be found')
            else:
                raise
        except requests.exceptions.Timeout as e:
            raise TimeoutException(f'Error in request: {e}')
        except Exception as e:
            raise JenkinsException(f'Error in request: {e}')
    
    def get_info(self, query: Optional[str] = None) -> dict:
        """获取Jenkins综合信息"""
        url = INFO
        if query:
            url = url + query
        response = self.jenkins_open(requests.Request('GET', self._build_url(url)))
        return json.loads(response)

    def get_whoami(self, depth: int = 0) -> dict:
        """获取当前用户信息"""
        url = WHOAMI_URL % {'depth': depth}
        response = self.jenkins_open(requests.Request('GET', self._build_url(url)))
        return json.loads(response)

    def get_version(self) -> str:
        """获取Jenkins版本"""
        req = requests.Request('GET', self._build_url(''))
        req.headers['X-Jenkins'] = '0.0'
        response = self.jenkins_request(req, add_crumb=False, resolve_auth=True)
        return response.headers.get('X-Jenkins', 'unknown')

    # ========== Job管理方法 ==========

    def get_job_info(self, name: str, depth: int = 0, fetch_all_builds: bool = False) -> dict:
        """获取Job信息"""
        folder_url, short_name = self._get_job_folder(name)
        response = self.jenkins_open(requests.Request(
            'GET', self._build_url(JOB_INFO, locals())
        ))
        if fetch_all_builds:
            return self._add_missing_builds(json.loads(response))
        return json.loads(response)

    def _add_missing_builds(self, data: dict) -> dict:
        """补全build列表（Jenkins默认只返回100条）"""
        if not data.get("builds"):
            return data
        oldest_loaded = data["builds"][-1]["number"]
        first_build = data["firstBuild"]["number"] if data.get("firstBuild") else oldest_loaded
        if oldest_loaded == first_build:
            return data

        folder_url, short_name = self._get_job_folder(data.get("fullName", ""))
        response = self.jenkins_open(requests.Request(
            'GET', self._build_url(ALL_BUILDS, locals())
        ))
        if response:
            data["builds"] = json.loads(response).get("allBuilds", [])
        return data

    def get_job_name(self, name: str) -> Optional[str]:
        """检查Job是否存在"""
        folder_url, short_name = self._get_job_folder(name)
        try:
            response = self.jenkins_open(requests.Request(
                'GET', self._build_url(JOB_NAME, locals())
            ))
            return json.loads(response)['name']
        except NotFoundException:
            return None

    def job_exists(self, name: str) -> bool:
        """检查Job是否存在"""
        return self.get_job_name(name) is not None

    def get_all_jobs(self, folder_depth: Optional[int] = None, folder_depth_per_request: int = 10) -> list:
        """获取所有Job（支持文件夹嵌套）"""
        jobs_query = 'jobs'
        for _ in range(folder_depth_per_request):
            jobs_query = JOBS_QUERY_TREE % jobs_query
        jobs_query = JOBS_QUERY % jobs_query

        jobs_list = []
        jobs = [(0, [], self.get_info(query=jobs_query)['jobs'])]

        for lvl, root, lvl_jobs in jobs:
            if not isinstance(lvl_jobs, list):
                lvl_jobs = [lvl_jobs]

            for job in lvl_jobs:
                path = root + [job['name']]
                if 'fullname' not in job:
                    job['fullname'] = '/'.join(path)
                jobs_list.append(job)

                if 'jobs' in job and isinstance(job['jobs'], list):
                    if folder_depth is None or lvl < folder_depth:
                        children = job['jobs']
                        if any('url' not in child for child in job['jobs']):
                            url_path = ''.join(['/job/' + p for p in path])
                            children = self.get_info(url_path + '/api/json?tree=jobs[url,name]')['jobs']
                        jobs.append((lvl + 1, path, children))

        return jobs_list

    def get_job_config(self, name: str) -> str:
        """获取Job配置XML"""
        folder_url, short_name = self._get_job_folder(name)
        return self.jenkins_open(requests.Request('GET', self._build_url(CONFIG_JOB, locals())))

    def create_job(self, name: str, config_xml: str) -> None:
        """创建Job"""
        folder_url, short_name = self._get_job_folder(name)
        if self.job_exists(name):
            raise JenkinsException(f'job[{name}] already exists')

        self.jenkins_open(requests.Request(
            'POST', self._build_url(CREATE_JOB, locals()),
            data=config_xml.encode('utf-8'),
            headers=DEFAULT_HEADERS
        ))

        if not self.job_exists(name):
            raise JenkinsException(f'create[{name}] failed')

    def reconfig_job(self, name: str, config_xml: str) -> None:
        """更新Job配置"""
        folder_url, short_name = self._get_job_folder(name)
        self.jenkins_open(requests.Request(
            'POST', self._build_url(CONFIG_JOB, locals()),
            data=config_xml.encode('utf-8'),
            headers=DEFAULT_HEADERS
        ))

    def delete_job(self, name: str) -> None:
        """删除Job"""
        folder_url, short_name = self._get_job_folder(name)
        self.jenkins_open(requests.Request('POST', self._build_url(DELETE_JOB, locals())))
        if self.job_exists(name):
            raise JenkinsException(f'delete[{name}] failed')

    def copy_job(self, from_name: str, to_name: str) -> None:
        """复制Job"""
        from_folder_url, from_short_name = self._get_job_folder(from_name)
        to_folder_url, to_short_name = self._get_job_folder(to_name)

        if from_folder_url != to_folder_url:
            raise JenkinsException('copy failed: source and destination folder must be the same')

        self.jenkins_open(requests.Request(
            'POST', self._build_url(COPY_JOB, locals())
        ))

        if not self.job_exists(to_name):
            raise JenkinsException(f'copy[{from_name} to {to_name}] failed')

    def rename_job(self, from_name: str, to_name: str) -> None:
        """重命名Job"""
        from_folder_url, from_short_name = self._get_job_folder(from_name)
        to_folder_url, to_short_name = self._get_job_folder(to_name)

        if from_folder_url != to_folder_url:
            raise JenkinsException('rename failed: source and destination folder must be the same')

        self.jenkins_open(requests.Request(
            'POST', self._build_url(RENAME_JOB, locals())
        ))

        if not self.job_exists(to_name):
            raise JenkinsException(f'rename[{from_name} to {to_name}] failed')

    def enable_job(self, name: str) -> None:
        """启用Job"""
        folder_url, short_name = self._get_job_folder(name)
        self.jenkins_open(requests.Request('POST', self._build_url(ENABLE_JOB, locals())))

    def disable_job(self, name: str) -> None:
        """禁用Job"""
        folder_url, short_name = self._get_job_folder(name)
        self.jenkins_open(requests.Request('POST', self._build_url(DISABLE_JOB, locals())))

    def set_next_build_number(self, name: str, number: int) -> None:
        """设置下一个构建号"""
        folder_url, short_name = self._get_job_folder(name)
        self.jenkins_open(requests.Request(
            'POST', self._build_url(SET_JOB_BUILD_NUMBER, locals()),
            data=f"nextBuildNumber={number}".encode('utf-8')
        ))

    def build_job_url(self, name: str, parameters: Optional[dict] = None, token: Optional[str] = None) -> str:
        """获取构建URL"""
        folder_url, short_name = self._get_job_folder(name)

        if parameters:
            if token:
                if isinstance(parameters, list):
                    parameters.append(('token', token))
                elif isinstance(parameters, dict):
                    parameters.update({'token': token})
                else:
                    raise JenkinsException('parameters can be dict or list of tuples')
            return self._build_url(BUILD_WITH_PARAMS_JOB, locals()) + '?' + urllib.parse.urlencode(parameters)
        elif token:
            return self._build_url(BUILD_JOB, locals()) + '?' + urllib.parse.urlencode({'token': token})
        else:
            return self._build_url(BUILD_JOB, locals())

    def build_job(self, name: str, parameters: Optional[dict] = None, token: Optional[str] = None) -> int:
        """触发构建，返回队列ID"""
        response = self.jenkins_request(requests.Request(
            'POST', self.build_job_url(name, parameters, token)
        ))

        location = response.headers.get('Location')
        if not location:
            raise JenkinsException("Header 'Location' not found in response")

        if location.endswith('/'):
            location = location[:-1]

        return int(location.split('/')[-1])

    # ========== Build管理方法 ==========

    def get_build_info(self, name: str, number: int, depth: int = 0) -> dict:
        """获取Build信息"""
        folder_url, short_name = self._get_job_folder(name)
        response = self.jenkins_open(requests.Request(
            'GET', self._build_url(BUILD_INFO, locals())
        ))
        return json.loads(response)

    def get_build_console_output(self, name: str, number: int) -> str:
        """获取构建日志"""
        folder_url, short_name = self._get_job_folder(name)
        return self.jenkins_open(requests.Request(
            'GET', self._build_url(BUILD_CONSOLE_OUTPUT, locals())
        ))

    def get_build_artifact(self, name: str, number: int, artifact: str) -> dict:
        """获取构建制品信息
        
        参数:
            name: 任务名称
            number: 构建编号
            artifact: 制品相对路径 (如 "data.txt")
        
        返回:
            制品信息
        """
        folder_url, short_name = self._get_job_folder(name)
        try:
            response = self.jenkins_open(requests.Request(
                'GET', self._build_url(BUILD_ARTIFACT, locals())))
            if response:
                try:
                    return json.loads(response)
                except ValueError:
                    return {'artifact': artifact, 'content': response}
            raise JenkinsException(f'job[{name}] number[{number}] artifact not found')
        except requests.exceptions.HTTPError:
            raise JenkinsException(f'job[{name}] number[{number}] not found')

    def get_build_artifact_as_bytes(self, name: str, number: int, artifact: str) -> bytes:
        """获取构建制品 (原始字节)
        
        参数:
            name: 任务名称
            number: 构建编号
            artifact: 制品相对路径 (如 "data.txt")
        
        返回:
            制品内容 (bytes)
        """
        folder_url, short_name = self._get_job_folder(name)
        try:
            response = self.jenkins_request(
                requests.Request('GET', self._build_url(BUILD_ARTIFACT, locals())),
                add_crumb=True
            )
            return response.content
        except requests.exceptions.HTTPError:
            raise JenkinsException(f'artifact {artifact} not found in job[{name}] number[{number}]')

    def get_build_artifact_to_file(self, name: str, number: int, artifact: str, path: str) -> dict:
        """下载构建制品到本地文件
        
        参数:
            name: 任务名称
            number: 构建编号
            artifact: 制品相对路径 (如 "data.txt")
            path: 本地保存路径
        
        返回:
            {'file': path, 'size': bytes}
        """
        data = self.get_build_artifact_as_bytes(name, number, artifact)
        import os
        with open(path, 'wb') as f:
            f.write(data)
        return {'file': path, 'size': len(data)}

    def get_build_env_vars(self, name: str, number: int) -> dict:
        """获取构建的环境变量

        优先尝试 injectedEnvVars API（EnvInject插件），
        失败时从 build info actions 中提取参数和环境变量。

        参数:
            name: 任务名称
            number: 构建编号

        返回:
            {key: value, ...} 环境变量字典
        """
        folder_url, short_name = self._get_job_folder(name)
        try:
            response = self.jenkins_open(requests.Request(
                'GET', self._build_url(BUILD_ENV_VARS, locals())
            ))
            data = json.loads(response)
            return data.get('envMap', {})
        except Exception:
            info = self.get_build_info(name, number, depth=2)
            env = {}
            for action in info.get('actions', []):
                cls = action.get('_class', '')
                if 'ParametersAction' in cls:
                    for p in action.get('parameters', []):
                        env[p.get('name', '')] = str(p.get('value', ''))
                elif 'EnvironmentContributingAction' in cls:
                    for k, v in action.get('env', {}).items():
                        env[k] = str(v)
                elif 'EnvironmentAction' in cls:
                    for k, v in action.get('environment', {}).items():
                        env[k] = str(v)
            return env

    def get_build_artifacts(self, name: str, number: int) -> list:
        """获取构建所有制品列表
        
        参数:
            name: 任务名称
            number: 构建编号
        
        返回:
            制品列表 [{relativePath, displayPath, fileName}, ...]
        """
        info = self.get_build_info(name, number)
        return info.get('artifacts', [])

    def get_running_builds(self) -> list:
        """获取运行中的构建"""
        builds = []
        nodes = self.get_nodes()

        for node in nodes:
            node_name = node.get('displayName', '')
            if node_name in ['Built-In Node']:
                node_name = '(master)'
            try:
                info = self.get_node_info(node_name, depth=2)
            except Exception:
                continue

            for executor in info.get('executors', []):
                executable = executor.get('currentExecutable')
                if executable and 'number' in executable:
                    url = executable.get('url', '')
                    path = urllib.parse.urlparse(url).path
                    match = re.search(r'/job/([^/]+)/', path)
                    job_name = match.group(1) if match else 'unknown'

                    builds.append({
                        'name': job_name,
                        'number': executable['number'],
                        'url': url,
                        'node': node_name,
                        'executor': executor.get('number')
                    })

        return builds

    def stop_build(self, name: str, number: int) -> None:
        """停止构建"""
        folder_url, short_name = self._get_job_folder(name)
        self.jenkins_open(requests.Request('POST', self._build_url(STOP_BUILD, locals())))

    def delete_build(self, name: str, number: int) -> None:
        """删除构建记录"""
        folder_url, short_name = self._get_job_folder(name)
        self.jenkins_open(requests.Request('POST', self._build_url(DELETE_BUILD, locals())))

    def wipeout_job_workspace(self, name: str) -> None:
        """清空工作区"""
        folder_url, short_name = self._get_job_folder(name)
        self.jenkins_open(requests.Request('POST', self._build_url(WIPEOUT_JOB_WORKSPACE, locals())))

    # ========== Queue管理方法 ==========

    def get_queue_info(self) -> list:
        """获取队列信息"""
        response = self.jenkins_open(requests.Request('GET', self._build_url(Q_INFO)))
        return json.loads(response).get('items', [])

    def get_queue_item(self, number: int, depth: int = 0) -> dict:
        """获取队列项"""
        response = self.jenkins_open(requests.Request(
            'GET', self._build_url(Q_ITEM, locals())
        ))
        return json.loads(response)

    def cancel_queue(self, id: int) -> None:
        """取消队列项"""
        self.jenkins_open(requests.Request(
            'POST', self._build_url(CANCEL_QUEUE, locals())
        ))

    # ========== Node管理方法 ==========

    def get_nodes(self, depth: int = 0) -> list:
        """获取节点列表"""
        response = self.jenkins_open(requests.Request(
            'GET', self._build_url(NODE_LIST, locals())
        ))
        return json.loads(response).get('computer', [])

    def get_node_info(self, name: str, depth: int = 0) -> dict:
        """获取节点详情"""
        if name.lower() == 'built-in node':
            name = '(master)'
        response = self.jenkins_open(requests.Request(
            'GET', self._build_url(NODE_INFO, locals())
        ))
        return json.loads(response)

    def node_exists(self, name: str) -> bool:
        """检查节点是否存在"""
        try:
            self.get_node_info(name)
            return True
        except JenkinsException:
            return False

    def get_node_config(self, name: str) -> str:
        """获取节点配置"""
        return self.jenkins_open(requests.Request(
            'GET', self._build_url(CONFIG_NODE, locals())
        ))

    def create_node(
            self,
            name: str,
            numExecutors: int = 2,
            nodeDescription: Optional[str] = None,
            remoteFS: str = '/var/lib/jenkins',
            labels: Optional[str] = None,
            exclusive: bool = False,
            launcher: str = LAUNCHER_COMMAND,
            launcher_params: Optional[dict] = None,
            config_xml: Optional[str] = None
    ) -> None:
        """创建节点"""
        if self.node_exists(name):
            raise JenkinsException(f'node[{name}] already exists')

        if config_xml:
            self.jenkins_open(requests.Request(
                'POST', self._build_url(CREATE_NODE) + '?name=' + urllib.parse.quote(name),
                data=config_xml.encode('utf-8'),
                headers=DEFAULT_HEADERS
            ))
        else:
            mode = 'EXCLUSIVE' if exclusive else 'NORMAL'

            inner_params = {
                'nodeDescription': nodeDescription or '',
                'numExecutors': numExecutors,
                'remoteFS': remoteFS,
                'labelString': labels or '',
                'mode': mode,
                'retentionStrategy': {
                    'stapler-class': 'hudson.slaves.RetentionStrategy$Always'
                },
                'nodeProperties': {'stapler-class-bag': 'true'},
                'launcher': (launcher_params or {})
            }
            launcher_params = launcher_params or {}
            launcher_params['stapler-class'] = launcher

            params = {
                'name': name,
                'type': NODE_TYPE,
                'json': json.dumps(inner_params)
            }

            self.jenkins_open(requests.Request(
                'POST', self._build_url(CREATE_NODE, locals()),
                data=params
            ))

        if not self.node_exists(name):
            raise JenkinsException(f'create[{name}] failed')

    def reconfig_node(self, name: str, config_xml: str) -> None:
        """更新节点配置"""
        self.jenkins_open(requests.Request(
            'POST', self._build_url(CONFIG_NODE, locals()),
            data=config_xml.encode('utf-8'),
            headers=DEFAULT_HEADERS
        ))

    def delete_node(self, name: str) -> None:
        """删除节点"""
        if name.lower() in ['built-in node', '(master)', 'master']:
            raise JenkinsException('cannot delete built-in node')

        self.get_node_info(name)
        self.jenkins_open(requests.Request('POST', self._build_url(DELETE_NODE, locals())))

        if self.node_exists(name):
            raise JenkinsException(f'delete[{name}] failed')

    def disable_node(self, name: str, msg: str = '') -> None:
        """禁用节点"""
        info = self.get_node_info(name)
        if info.get('offline'):
            return
        self.jenkins_open(requests.Request(
            'POST', self._build_url(TOGGLE_OFFLINE, locals())
        ))

    def enable_node(self, name: str) -> None:
        """启用节点"""
        info = self.get_node_info(name)
        if not info.get('offline'):
            return
        self.jenkins_open(requests.Request(
            'POST', self._build_url(TOGGLE_OFFLINE, locals())
        ))

    # ========== Plugin管理方法 ==========

    def get_plugins(self, depth: int = 2) -> dict:
        """获取插件列表"""
        response = self.jenkins_open(requests.Request(
            'GET', self._build_url(PLUGIN_INFO, {'depth': depth})
        ))
        return json.loads(response).get('plugins', [])

    def get_plugin_info(self, short_name: str, depth: int = 2) -> Optional[dict]:
        """获取插件详情"""
        plugins = self.get_plugins(depth)
        for plugin in plugins:
            if plugin.get('shortName') == short_name:
                return plugin
        return None

    def install_plugin(self, short_name: str, version: Optional[str] = None) -> dict:
        """安装插件

        参数:
            short_name: 插件短名称
            version: 可选版本号，不指定则安装最新版
        """
        payload = {'dynamicLoad': True, 'plugins': [{'name': short_name}]}
        if version:
            payload['plugins'][0]['version'] = version
        headers = {'Content-Type': 'application/json'}
        self.jenkins_open(requests.Request(
            'POST', self._build_url(PLUGIN_INSTALL),
            data=json.dumps(payload), headers=headers
        ))
        return {'status': 'installed', 'plugin': short_name, 'version': version or 'latest'}

    def uninstall_plugin(self, short_name: str) -> None:
        """卸载插件"""
        self.jenkins_open(requests.Request(
            'POST', self._build_url(PLUGIN_UNINSTALL, {'short_name': short_name})
        ))

    def enable_plugin(self, short_name: str) -> None:
        """启用插件（通过Groovy脚本）"""
        script = f'jenkins.model.Jenkins.instance.pluginManager.getPlugin("{short_name}")?.enable()'
        self.run_script(script)

    def disable_plugin(self, short_name: str) -> None:
        """禁用插件（通过Groovy脚本）"""
        script = f'jenkins.model.Jenkins.instance.pluginManager.getPlugin("{short_name}")?.disable()'
        self.run_script(script)

    # ========== View管理方法 ==========

    def get_views(self) -> list:
        """获取视图列表"""
        return self.get_info().get('views', [])

    def view_exists(self, name: str) -> bool:
        """检查视图是否存在"""
        try:
            return self.get_view_name(name) is not None
        except JenkinsException:
            return False

    def get_view_name(self, name: str) -> Optional[str]:
        """检查视图是否存在"""
        folder_url, short_name = self._get_job_folder(name)
        try:
            response = self.jenkins_open(requests.Request(
                'GET', self._build_url(VIEW_NAME, locals())
            ))
            actual = json.loads(response).get('name')
            if actual == name or (actual == 'All' and short_name == 'All'):
                return name
        except Exception:
            pass
        return None

    def create_view(self, name: str, config_xml: str) -> None:
        """创建视图"""
        folder_url, short_name = self._get_job_folder(name)
        if self.view_exists(name):
            raise JenkinsException(f'view[{name}] already exists')

        self.jenkins_open(requests.Request(
            'POST', self._build_url(CREATE_VIEW, locals()),
            data=config_xml.encode('utf-8'),
            headers=DEFAULT_HEADERS
        ))

        if not self.view_exists(name):
            raise JenkinsException(f'create[{name}] failed')

    def get_view_config(self, name: str) -> str:
        """获取视图配置"""
        folder_url, short_name = self._get_job_folder(name)
        return self.jenkins_open(requests.Request(
            'GET', self._build_url(CONFIG_VIEW, locals())
        ))

    def reconfig_view(self, name: str, config_xml: str) -> None:
        """更新视图配置"""
        folder_url, short_name = self._get_job_folder(name)
        self.jenkins_open(requests.Request(
            'POST', self._build_url(CONFIG_VIEW, locals()),
            data=config_xml.encode('utf-8'),
            headers=DEFAULT_HEADERS
        ))

    def delete_view(self, name: str) -> None:
        """删除视图"""
        folder_url, short_name = self._get_job_folder(name)
        self.jenkins_open(requests.Request('POST', self._build_url(DELETE_VIEW, locals())))

        if self.view_exists(name):
            raise JenkinsException(f'delete[{name}] failed')

    # ========== Script执行方法 ==========

    def run_script(self, script: str, node: Optional[str] = None) -> str:
        """执行Groovy脚本"""
        result_prefix = 'Result: '
        if node:
            url = self._build_url(NODE_SCRIPT_TEXT, {'node': node})
        else:
            url = self._build_url(SCRIPT_TEXT)

        result = self.jenkins_open(requests.Request('POST', url, data={'script': script.encode('utf-8')}))

        if result.startswith(result_prefix):
            return result[len(result_prefix):].rstrip('\n')

        if result.startswith('Result: '):
            return result[8:].rstrip('\n')

        raise JenkinsException(result)

    def quiet_down(self) -> None:
        """Quiet Down Jenkins - 进入静默模式，不再接受新构建"""
        self.jenkins_open(requests.Request('POST', self._build_url(QUIET_DOWN, {})))

    def cancel_quiet_down(self) -> None:
        """Cancel Quiet Down - 取消静默模式"""
        self.jenkins_open(requests.Request('POST', self._build_url(CANCEL_QUIET_DOWN, {})))

    def safe_restart(self) -> None:
        """Safe Restart - 等待所有运行中的构建完成后重启"""
        self.jenkins_open(requests.Request('POST', self._build_url(SAFE_RESTART, {})))

    def restart(self) -> None:
        """强制重启 - 立即重启Jenkins"""
        self.jenkins_open(requests.Request('POST', self._build_url(RESTART, {})))

    def reload_configuration(self) -> None:
        """重载配置 - 从磁盘重新加载所有配置"""
        self.jenkins_open(requests.Request('POST', self._build_url(RELOAD, {})))
