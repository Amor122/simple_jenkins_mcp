"""Jenkins MCP Tools - 公共工具"""

import os
from functools import wraps
from typing import Any, Callable, Set


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