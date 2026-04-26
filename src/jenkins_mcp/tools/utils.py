"""Jenkins MCP Tools - 公共工具"""

import os
from functools import wraps
from typing import Callable, TypeVar

F = TypeVar('F')


def check_read_only(tags: frozenset) -> None:
    """检查只读模式"""
    read_only = os.getenv('JENKINS_READ_ONLY', 'false').lower() == 'true'
    if read_only and tags != frozenset({'read'}):
        raise PermissionError("只读模式下禁止此操作")


def read_only(tags: frozenset = frozenset({'read'})):
    """只读检查装饰器 - 默认tags为{'read'}，即只读操作不需要额外权限"""
    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            check_read_only(tags)
            return await func(*args, **kwargs)
        return wrapper  # type: ignore
    return decorator


def write_only(func: F) -> F:
    """只写操作装饰器"""
    return read_only(frozenset({'write'}))(func)


def admin_only(func: F) -> F:
    """管理员操作装饰器"""
    return read_only(frozenset({'admin'}))(func)