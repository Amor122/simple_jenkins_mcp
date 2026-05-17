"""Jenkins MCP Tools - 公共工具"""

import os
from functools import wraps
from typing import Any, Callable, Optional, Set


def check_read_only(tags: Set[str]) -> None:
    """检查只读模式"""
    read_only = os.getenv('JENKINS_READ_ONLY', 'false').lower() == 'true'
    if read_only and 'read' not in tags:
        raise PermissionError("只读模式下禁止此操作")


def admin_only(func: Callable[..., Any]) -> Callable[..., Any]:
    """管理员操作装饰器"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        check_read_only({'admin'})
        return await func(*args, **kwargs)
    return wrapper


def write_only(func: Callable[..., Any]) -> Callable[..., Any]:
    """只写操作装饰器"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        check_read_only({'write'})
        return await func(*args, **kwargs)
    return wrapper


def create_jenkins_client(username: str, api_token: str):
    """使用指定的用户名和API Token创建Jenkins客户端

    参数:
        username: Jenkins用户名
        api_token: Jenkins API Token（或密码）

    返回:
        Jenkins客户端实例

    异常:
        ValueError: Jenkins URL未配置
    """
    from jenkins_mcp.jenkins import Jenkins

    url = os.getenv('JENKINS_URL', '')
    if not url:
        raise ValueError("请在 .env 中配置 JENKINS_URL 环境变量")

    timeout = int(os.getenv('JENKINS_TIMEOUT', '30'))
    verify_ssl = os.getenv('JENKINS_VERIFY_SSL', 'true').lower() == 'true'

    return Jenkins(
        url=url,
        username=username,
        password=api_token,
        timeout=timeout,
        verify_ssl=verify_ssl,
    )


async def verify_credentials(username: str, api_token: str) -> dict:
    """验证Jenkins账户和API Token的有效性及管理员权限

    参数:
        username: Jenkins用户名
        api_token: Jenkins API Token

    返回:
        凭据验证结果（用户信息 + 管理员状态）

    异常:
        PermissionError: 凭据无效
    """
    jk = create_jenkins_client(username, api_token)

    try:
        whoami = jk.get_whoami()
    except Exception as e:
        raise PermissionError(
            f"Jenkins账户或API Token验证失败: {e}\n"
            f"请检查用户名 [{username}] 和 API Token 是否正确。"
        )

    user_id = whoami.get('id', 'unknown')
    full_name = whoami.get('fullName', '')

    check_admin_script = "jenkins.model.Jenkins.instance.hasPermission(jenkins.model.Jenkins.ADMINISTER).toString()"
    try:
        result = jk.run_script(check_admin_script)
        is_admin = result.strip() == 'true'
    except Exception as e:
        is_admin = "unknown"

    return {
        "user_id": user_id,
        "full_name": full_name,
        "is_admin": is_admin,
    }