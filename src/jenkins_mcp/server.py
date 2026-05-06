"""
Jenkins MCP Server

基于FastMCP框架的Jenkins管理工具

优先级: Jenkins源码 > python-jenkins > 其他参考资料

环境变量配置 (.env文件支持):
    JENKINS_URL: Jenkins地址 (默认: http://localhost:8080)
    JENKINS_USERNAME: 用户名 (默认: admin)
    JENKINS_PASSWORD: 密码或API Token (默认: 空)
    JENKINS_TIMEOUT: 超时时间(默认: 30秒)
    JENKINS_VERIFY_SSL: 是否验证SSL(默认: true)
    JENKINS_READ_ONLY: 只读模式(默认: false)
    JENKINS_CONFIG_PATH: .env配置文件路径(默认: .env)
"""

import os
import sys
from typing import Optional

try:
    from dotenv import load_dotenv
except ImportError:
    print("请安装python-dotenv: pip install python-dotenv")
    sys.exit(1)

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    print("请安装fastmcp: pip install mcp")
    sys.exit(1)

from jenkins_mcp.jenkins import Jenkins
from jenkins_mcp import tools
from jenkins_mcp.tools.utils import write_only


def _load_env_config(config_path: Optional[str] = None) -> None:
    """从.env文件加载环境变量"""
    if config_path is None:
        config_path = os.getenv('JENKINS_CONFIG_PATH', '.env')
    
    # 可能的.env位置列表
    possible_paths = []
    
    # 1. 如果是绝对路径
    if os.path.isabs(config_path):
        possible_paths.append(config_path)
    else:
        # 2. 当前工作目录
        possible_paths.append(os.path.join(os.getcwd(), config_path))
        # 3. 当前工作目录的上层目录（如果.env在项目根目录）
        possible_paths.append(os.path.join(os.getcwd(), 'jenkins_mcp', config_path))
        possible_paths.append(os.path.join(os.getcwd(), '..', config_path))
        # 4. 脚本所在目录的上层（jenkins_mcp/目录）
        script_dir = os.path.dirname(os.path.dirname(__file__))
        possible_paths.append(os.path.join(script_dir, config_path))
        possible_paths.append(os.path.join(script_dir, '..', config_path))
    
    for path in possible_paths:
        path = os.path.normpath(path)
        if os.path.exists(path):
            load_dotenv(path)
            return


_load_env_config()


# 全局Jenkins客户端
_jenkins_client: Optional[Jenkins] = None


def get_jenkins_client() -> Jenkins:
    """获取Jenkins客户端实例"""
    global _jenkins_client
    
    if _jenkins_client is None:
        url = os.getenv('JENKINS_URL', 'http://localhost:8080')
        username = os.getenv('JENKINS_USERNAME', 'admin')
        password = os.getenv('JENKINS_PASSWORD', '')
        timeout = int(os.getenv('JENKINS_TIMEOUT', '30'))
        verify_ssl = os.getenv('JENKINS_VERIFY_SSL', 'true').lower() == 'true'
        
        if not url:
            raise ValueError("请设置JENKINS_URL环境变量")
        
        _jenkins_client = Jenkins(
            url=url,
            username=username,
            password=password,
            timeout=timeout,
            verify_ssl=verify_ssl
        )
    
    return _jenkins_client


# 创建MCP服务器
mcp = FastMCP("jenkins-mcp-server")


# ==================== 工具定义 ====================

# Job管理工具
@mcp.tool()
async def get_all_jobs(folder_depth: int = None):
    """获取所有Job列表"""
    return await tools.job.get_all_jobs(get_jenkins_client(), folder_depth)


@mcp.tool()
async def get_job(name: str, depth: int = 0):
    """获取指定Job信息"""
    return await tools.job.get_job(get_jenkins_client(), name, depth)


@mcp.tool()
async def get_job_config(name: str):
    """获取Job配置XML"""
    return await tools.job.get_job_config(get_jenkins_client(), name)


@mcp.tool()
async def set_job_config(name: str, config_xml: str):
    """设置Job配置"""
    return await tools.job.set_job_config(get_jenkins_client(), name, config_xml)


@mcp.tool()
async def create_job(name: str, config_xml: str):
    """创建新Job"""
    return await tools.job.create_job(get_jenkins_client(), name, config_xml)


@mcp.tool()
async def delete_job(name: str):
    """删除Job"""
    return await tools.job.delete_job(get_jenkins_client(), name)


@mcp.tool()
async def copy_job(from_name: str, to_name: str):
    """复制Job"""
    return await tools.job.copy_job(get_jenkins_client(), from_name, to_name)


@mcp.tool()
async def enable_job(name: str):
    """启用Job"""
    return await tools.job.enable_job(get_jenkins_client(), name)


@mcp.tool()
async def disable_job(name: str):
    """禁用Job"""
    return await tools.job.disable_job(get_jenkins_client(), name)

@mcp.tool()
async def build_job(name: str, parameters: dict = None, token: str = None):
    """触发构建"""
    return await tools.job.build_job(get_jenkins_client(), name, parameters, token)

@mcp.tool()
async def rename_job(name: str, new_name: str):
    """重命名Job"""
    return await tools.job.rename_job(get_jenkins_client(), name, new_name)

@mcp.tool()
async def set_next_build_number(name: str, number: int):
    """设置下一个构建号"""
    return await tools.job.set_next_build_number(get_jenkins_client(), name, number)

@mcp.tool()
async def wipeout_workspace(name: str):
    """清空工作区"""
    return await tools.job.wipeout_workspace(get_jenkins_client(), name)

@mcp.tool()
async def job_exists(name: str):
    """检查Job是否存在"""
    return await tools.job.job_exists(get_jenkins_client(), name)

@mcp.tool()
async def check_jenkinsfile_syntax(jenkinsfile: str):
    """检查Pipeline语法"""
    return await tools.job.check_jenkinsfile_syntax(get_jenkins_client(), jenkinsfile)

# Build管理工具
@mcp.tool()
async def get_build(name: str, number: int, depth: int = 0):
    """获取Build信息"""
    return await tools.build.get_build(get_jenkins_client(), name, number, depth)


@mcp.tool()
async def get_build_console_output(name: str, number: int, offset: int = 0, limit: int = None):
    """获取构建日志"""
    return await tools.build.get_build_console_output(
        get_jenkins_client(), name, number, offset, limit
    )


@mcp.tool()
async def get_running_builds():
    """获取运行中的Build"""
    return await tools.build.get_running_builds(get_jenkins_client())


@mcp.tool()
async def stop_build(name: str, number: int):
    """停止Build"""
    return await tools.build.stop_build(get_jenkins_client(), name, number)


@mcp.tool()
async def delete_build(name: str, number: int):
    """删除Build记录"""
    return await tools.build.delete_build(get_jenkins_client(), name, number)

@mcp.tool()
async def stop_all_builds(name: str = None):
    """停止所有运行中的Build"""
    return await tools.build.stop_all_builds(get_jenkins_client(), name)

@mcp.tool()
async def get_build_artifacts(name: str, number: int):
    """获取Build的所有归档制品列表"""
    return await tools.build.get_build_artifacts(get_jenkins_client(), name, number)


@mcp.tool()
async def get_build_artifact(name: str, number: int, artifact: str):
    """获取Build制品内容（文本）"""
    return await tools.build.get_build_artifact(get_jenkins_client(), name, number, artifact)


@mcp.tool()
async def download_build_artifact(name: str, number: int, artifact: str, path: str):
    """下载Build特定制品到本地文件"""
    return await tools.build.download_build_artifact(get_jenkins_client(), name, number, artifact, path)


@mcp.tool()
async def download_all_artifacts(name: str, number: int, output_dir: str):
    """下载Build的所有制品到本地目录"""
    return await tools.build.download_all_artifacts(get_jenkins_client(), name, number, output_dir)


# Queue管理工具
@mcp.tool()
async def get_all_queue_items():
    """获取所有队列项"""
    return await tools.queue.get_all_queue_items(get_jenkins_client())


@mcp.tool()
async def get_queue_item(id: int, depth: int = 0):
    """获取队列项详情"""
    return await tools.queue.get_queue_item(get_jenkins_client(), id, depth)


@mcp.tool()
async def get_queue_items_by_job(name: str):
    """获取指定Job的队列项"""
    return await tools.queue.get_queue_items_by_job(get_jenkins_client(), name)


@mcp.tool()
async def cancel_queue_item(id: int):
    """取消队列项"""
    return await tools.queue.cancel_queue_item(get_jenkins_client(), id)


@mcp.tool()
async def cancel_job_queue(name: str):
    """取消Job的队列"""
    return await tools.queue.cancel_job_queue(get_jenkins_client(), name)


@mcp.tool()
async def cancel_all_queue():
    """取消所有队列"""
    return await tools.queue.cancel_all_queue(get_jenkins_client())


# Node管理工具
@mcp.tool()
async def get_all_nodes(depth: int = 0):
    """获取所有节点"""
    return await tools.node.get_all_nodes(get_jenkins_client(), depth)


@mcp.tool()
async def get_node(name: str, depth: int = 2):
    """获取节点详情"""
    return await tools.node.get_node(get_jenkins_client(), name, depth)


@mcp.tool()
async def get_node_config(name: str):
    """获取节点配置"""
    return await tools.node.get_node_config(get_jenkins_client(), name)


@mcp.tool()
async def set_node_config(name: str, config_xml: str):
    """设置节点配置"""
    return await tools.node.set_node_config(get_jenkins_client(), name, config_xml)


@mcp.tool()
async def create_node(name: str, config_xml: str):
    """创建节点"""
    return await tools.node.create_node(get_jenkins_client(), name, config_xml)


@mcp.tool()
async def delete_node(name: str):
    """删除节点"""
    return await tools.node.delete_node(get_jenkins_client(), name)


@mcp.tool()
async def set_node_offline(name: str, message: str = ""):
    """设置节点离线"""
    return await tools.node.set_node_offline(get_jenkins_client(), name, message)


@mcp.tool()
async def set_node_online(name: str):
    """设置节点在线"""
    return await tools.node.set_node_online(get_jenkins_client(), name)

@mcp.tool()
async def node_exists(name: str):
    """检查节点是否存在"""
    return await tools.node.node_exists(get_jenkins_client(), name)


# Plugin管理工具
@mcp.tool()
async def get_all_plugins(depth: int = 2):
    """获取所有插件"""
    return await tools.plugin.get_all_plugins(get_jenkins_client(), depth)


@mcp.tool()
async def get_plugin(short_name: str, depth: int = 2):
    """获取插件详情"""
    return await tools.plugin.get_plugin(get_jenkins_client(), short_name, depth)


@mcp.tool()
async def get_plugins_with_problems():
    """获取有问题的插件"""
    return await tools.plugin.get_plugins_with_problems(get_jenkins_client())


# ==================== Lockable Resources Plugin管理工具 ====================

@mcp.tool()
async def get_all_lockable_resources():
    """获取所有锁资源"""
    return await tools.plugins_management.lockable_resources.get_all_lockable_resources(get_jenkins_client())


@mcp.tool()
async def get_lockable_resource(name: str):
    """获取指定锁资源详情"""
    return await tools.plugins_management.lockable_resources.get_lockable_resource(get_jenkins_client(), name)


@mcp.tool()
async def add_lockable_resource(name: str, labels: str = '', description: str = '', properties: dict = None):
    """添加锁资源
    
    参数:
        name: 资源名称
        labels: 可选，资源标签（多个用空格分隔）
        description: 可选，资源描述
        properties: 可选，键值对属性，如 {"key1": "value1", "key2": "value2"}
    """
    return await tools.plugins_management.lockable_resources.add_lockable_resource(
        get_jenkins_client(), name, labels, description, properties=properties
    )


@mcp.tool()
async def delete_lockable_resource(name: str):
    """删除指定锁资源
    
    参数:
        name: 资源名称
    """
    return await tools.plugins_management.lockable_resources.delete_lockable_resource(get_jenkins_client(), name)


@mcp.tool()
async def unlock_lockable_resource(name: str):
    """解锁指定锁资源"""
    return await tools.plugins_management.lockable_resources.unlock_lockable_resource(get_jenkins_client(), name)


@mcp.tool()
async def reserve_lockable_resource(name: str, user: str = 'admin', reason: str = ''):
    """预留指定锁资源
    
    参数:
        name: 资源名称
        user: 可选，预留用户（默认admin）
        reason: 可选，预留原因
    """
    return await tools.plugins_management.lockable_resources.reserve_lockable_resource(
        get_jenkins_client(), name, user, reason
    )


@mcp.tool()
async def unreserve_lockable_resource(name: str):
    """取消预留指定锁资源"""
    return await tools.plugins_management.lockable_resources.unreserve_lockable_resource(get_jenkins_client(), name)


@mcp.tool()
async def get_lockable_queue():
    """获取锁资源队列信息"""
    return await tools.plugins_management.lockable_resources.get_lockable_queue(get_jenkins_client())


@mcp.tool()
async def lockable_resource_exists(name: str):
    """检查锁资源是否存在"""
    return await tools.plugins_management.lockable_resources.lockable_resource_exists(get_jenkins_client(), name)


@mcp.tool()
async def set_lockable_resource_properties(name: str, properties: dict):
    """设置锁资源的属性（替换所有属性）
    
    参数:
        name: 资源名称
        properties: 键值对字典，如 {"key1": "value1", "key2": "value2"}
    """
    return await tools.plugins_management.lockable_resources.set_lockable_resource_properties(
        get_jenkins_client(), name, properties
    )


@mcp.tool()
async def set_lockable_resource_property(name: str, key: str, value: str):
    """设置锁资源的单个属性
    
    参数:
        name: 资源名称
        key: 属性键
        value: 属性值
    """
    return await tools.plugins_management.lockable_resources.set_lockable_resource_property(
        get_jenkins_client(), name, key, value
    )


@mcp.tool()
async def get_lockable_resource_property(name: str, key: str):
    """获取锁资源的单个属性值
    
    参数:
        name: 资源名称
        key: 属性键
    """
    return await tools.plugins_management.lockable_resources.get_lockable_resource_property(
        get_jenkins_client(), name, key
    )


@mcp.tool()
async def get_all_lockable_labels():
    """获取所有锁资源标签"""
    return await tools.plugins_management.lockable_resources.get_all_lockable_labels(get_jenkins_client())


@mcp.tool()
async def get_lockable_resources_by_label(label: str):
    """获取具有指定标签的所有锁资源"""
    return await tools.plugins_management.lockable_resources.get_lockable_resources_by_label(get_jenkins_client(), label)


# Label管理工具
@mcp.tool()
async def get_all_labels(depth: int = 2):
    """获取所有Label及关联节点"""
    return await tools.label.get_all_labels(get_jenkins_client(), depth)


@mcp.tool()
async def get_label(name: str, depth: int = 2):
    """获取指定Label详情"""
    return await tools.label.get_label(get_jenkins_client(), name, depth)


@mcp.tool()
async def get_nodes_by_label(label: str, depth: int = 2):
    """获取具有指定Label的所有节点"""
    return await tools.label.get_nodes_by_label(get_jenkins_client(), label, depth)


@mcp.tool()
async def get_label_load():
    """获取Label负载信息"""
    return await tools.label.get_label_load(get_jenkins_client())


# ==================== Cloud管理工具 ====================

@mcp.tool()
async def get_all_clouds():
    """获取所有云配置"""
    return await tools.cloud.get_all_clouds(get_jenkins_client())


@mcp.tool()
async def get_cloud_config(name: str):
    """获取指定云配置的详细信息"""
    return await tools.cloud.get_cloud_config(get_jenkins_client(), name)


@mcp.tool()
async def get_cloud_templates(cloud_name: str):
    """获取云的所有模板"""
    return await tools.cloud.get_cloud_templates(get_jenkins_client(), cloud_name)


@mcp.tool()
async def analyze_cloud_nodes(cloud_name: str = None):
    """分析云相关的节点
    
    参数:
        cloud_name: 可选，指定云名称
    """
    return await tools.cloud.analyze_cloud_nodes(get_jenkins_client(), cloud_name)


@mcp.tool()
async def analyze_cloud_availability(cloud_name: str = None):
    """分析云可用性和健康状态"""
    return await tools.cloud.analyze_cloud_availability(get_jenkins_client(), cloud_name)


@mcp.tool()
async def disable_cloud(cloud_name: str):
    """禁用云"""
    return await tools.cloud.disable_cloud(get_jenkins_client(), cloud_name)


@mcp.tool()
async def enable_cloud(cloud_name: str):
    """启用云"""
    return await tools.cloud.enable_cloud(get_jenkins_client(), cloud_name)


@mcp.tool()
async def delete_cloud(cloud_name: str):
    """删除云配置"""
    return await tools.cloud.delete_cloud(get_jenkins_client(), cloud_name)


@mcp.tool()
async def delete_template(cloud_name: str, template_name: str):
    """删除云模板"""
    return await tools.cloud.delete_template(get_jenkins_client(), cloud_name, template_name)


@mcp.tool()
async def create_kubernetes_cloud(name: str, server_url: str, namespace: str = "default",
                                   credentials_id: str = None, container_cap: int = 0):
    """创建Kubernetes云配置"""
    return await tools.cloud.create_kubernetes_cloud(
        get_jenkins_client(), name, server_url, namespace, credentials_id, container_cap
    )


@mcp.tool()
async def add_pod_template(cloud_name: str, template_config: dict):
    """添加Pod模板到Kubernetes云"""
    return await tools.cloud.add_pod_template(get_jenkins_client(), cloud_name, template_config)


@mcp.tool()
async def get_kubernetes_pods(namespace: str = None):
    """获取Kubernetes pods信息"""
    return await tools.cloud.get_kubernetes_pods(get_jenkins_client(), namespace)


@mcp.tool()
async def get_cloud_provisioning_stats():
    """获取云Provisioning统计"""
    return await tools.cloud.get_provisioning_stats(get_jenkins_client())


# ==================== Script管理工具 ====================

@mcp.tool()
async def run_groovy_script(script: str, node: str = None):
    """执行任意Groovy脚本 (用于访问Jenkins没有REST API的内部功能)
    
    参数:
        script: Groovy脚本代码
        node: 可选，在指定节点上执行（默认在master）
    
    返回:
        脚本执行结果
    """
    return await tools.script.run_groovy_script(get_jenkins_client(), script, node)


@mcp.tool()
async def get_jenkins_info():
    """获取Jenkins系统信息"""
    return await tools.script.get_jenkins_info(get_jenkins_client())


@mcp.tool()
async def get_jenkins_version():
    """获取Jenkins版本"""
    return await tools.script.get_jenkins_version(get_jenkins_client())


@mcp.tool()
async def get_whoami():
    """获取当前认证用户信息"""
    return await tools.script.get_whoami(get_jenkins_client())


# ==================== 主入口 ====================

def main():
    """主入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Jenkins MCP Server')
    parser.add_argument('--transport', '-t', default=None, choices=['stdio', 'sse', 'streamable-http'], help='传输方式 (默认: stdio)')
    parser.add_argument('--port', '-p', type=int, default=None, help='HTTP端口 (默认: 8000)')
    parser.add_argument('--host', default=None, help='监听地址 (默认: 0.0.0.0)')
    parser.add_argument('--config', '-c', default=None, help='.env配置文件路径')
    args = parser.parse_args()
    
    # 重新加载配置文件
    if args.config:
        _load_env_config(args.config)
    
    # 从环境变量读取配置（优先级：命令行 > 环境变量 > 默认值）
    transport = args.transport or os.getenv('MCP_TRANSPORT', os.getenv('JENKINS_TRANSPORT', 'stdio'))
    host = args.host or os.getenv('MCP_HOST', os.getenv('JENKINS_HOST', '0.0.0.0'))
    port = args.port or int(os.getenv('MCP_PORT', os.getenv('JENKINS_PORT', '8000')))
    url = os.getenv('JENKINS_URL')
    
    if not url:
        print("警告: 未设置JENKINS_URL环境变量", file=sys.stderr)
        print("\n请创建 .env 文件或设置环境变量:", file=sys.stderr)
        print("  JENKINS_URL=http://your-jenkins:8080", file=sys.stderr)
        print("  JENKINS_USERNAME=your_username", file=sys.stderr)
        print("  JENKINS_PASSWORD=your_token", file=sys.stderr)
        print("\n查看 .env.example 获取完整配置示例", file=sys.stderr)
    
    if transport == 'stdio':
        mcp.run(transport='stdio')
    else:
        mcp.settings.host = host
        mcp.settings.port = port
        mcp.run(transport=transport)


if __name__ == '__main__':
    main()