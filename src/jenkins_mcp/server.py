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
from jenkins_mcp import registrations


def _load_env_config(config_path: Optional[str] = None) -> None:
    """从.env文件加载环境变量"""
    if config_path is None:
        config_path = os.getenv('JENKINS_CONFIG_PATH', '.env')
    
    possible_paths = []
    
    if os.path.isabs(config_path):
        possible_paths.append(config_path)
    else:
        possible_paths.append(os.path.join(os.getcwd(), config_path))
        possible_paths.append(os.path.join(os.getcwd(), 'jenkins_mcp', config_path))
        possible_paths.append(os.path.join(os.getcwd(), '..', config_path))
        script_dir = os.path.dirname(os.path.dirname(__file__))
        possible_paths.append(os.path.join(script_dir, config_path))
        possible_paths.append(os.path.join(script_dir, '..', config_path))
    
    for path in possible_paths:
        path = os.path.normpath(path)
        if os.path.exists(path):
            load_dotenv(path)
            return


_load_env_config()


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

# 注册所有工具
registrations.register_all_tools(mcp)


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
    
    if args.config:
        _load_env_config(args.config)
    
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
    
    if transport == 'stdio':
        mcp.run(transport='stdio')
    else:
        mcp.settings.host = host
        mcp.settings.port = port
        mcp.run(transport=transport)


if __name__ == '__main__':
    main()