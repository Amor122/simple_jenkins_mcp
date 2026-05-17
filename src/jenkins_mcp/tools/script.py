"""
Jenkins MCP Server - Script执行工具模块

提供Groovy脚本执行功能，用于访问Jenkins内部API
"""

from jenkins_mcp.tools.utils import write_only, create_jenkins_client, verify_credentials


@write_only
async def run_groovy_script(jk, script: str) -> str:
    """执行任意Groovy脚本
    
    用于访问Jenkins没有REST API的内部功能
    
    参数:
        jk: Jenkins客户端
        script: Groovy脚本代码
    
    返回:
        脚本执行结果
    """
    return jk.run_script(script)


async def get_jenkins_info(jk) -> dict:
    """获取Jenkins系统信息
    
    返回:
        Jenkins系统信息
    """
    return jk.get_info()


async def get_jenkins_version(jk) -> str:
    """获取Jenkins版本
    
    返回:
        Jenkins版本号
    """
    return jk.get_version()


async def get_whoami(jk) -> dict:
    """获取当前认证用户信息
    
    返回:
        当前用户信息
    """
    return jk.get_whoami()


async def verify_jenkins_credentials(username: str, api_token: str) -> dict:
    """验证Jenkins账户和API Token的有效性及管理员权限
    
    使用指定的Jenkins用户名和API Token连接到Jenkins，
    验证凭据有效并检查该用户是否具有管理员权限。
    
    参数:
        username: Jenkins用户名
        api_token: Jenkins API Token
    
    返回:
        验证结果，包含用户ID、全名和管理员状态
    
    异常:
        PermissionError: 凭据无效或连接失败
    """
    return await verify_credentials(username, api_token)


async def get_system_message(jk) -> dict:
    """获取Jenkins系统消息（dashboard上显示的描述信息）"""
    info = jk.get_info()
    return {
        "system_message": info.get("description", ""),
    }


@write_only
async def set_system_message(username: str, api_token: str, message: str, confirm: bool = False) -> dict:
    """设置Jenkins系统消息

    需要提供具有管理员权限的Jenkins账户和API Token。
    第一次调用时不传 confirm=True 会返回确认信息，
    确认无误后第二次调用时传入 confirm=True 执行。
    """
    cred_info = await verify_credentials(username, api_token)
    if cred_info["is_admin"] is False:
        raise PermissionError(
            f"用户 [{cred_info['user_id']}] 没有管理员权限，无法设置系统消息。\n"
            f"请使用具有管理员权限的 Jenkins 账户和 API Token。"
        )
    admin_status = "已验证 ✓" if cred_info["is_admin"] is True else "无法自动验证，将交由 Jenkins 鉴权"
    if not confirm:
        preview = message[:200] + "..." if len(message) > 200 else message
        raise ValueError(
            f"⚠️  危险操作确认\n\n"
            f"操作: 设置 Jenkins 系统消息\n"
            f"当前用户: {cred_info['user_id']} ({cred_info['full_name']})\n"
            f"管理员身份: {admin_status}\n\n"
            f"消息内容:\n{preview}\n\n"
            f"如确认执行，请传入参数 confirm=True"
        )
    escaped = message.replace('\\', '\\\\').replace("'", "\\'").replace('\n', '\\n')
    script = f"Jenkins.getInstance().setSystemMessage('{escaped}'); Jenkins.getInstance().save()"
    jk = create_jenkins_client(username, api_token)
    jk.run_script(script)
    return {
        "success": True,
        "operation": "set_system_message",
        "triggered_by": cred_info["user_id"],
        "message": "Jenkins 系统消息已更新。",
    }


@write_only
async def safe_restart_jenkins(username: str, api_token: str, confirm: bool = False) -> dict:
    """安全重启Jenkins - 等待所有运行中的构建完成后重启
    
    需要提供具有管理员权限的Jenkins账户和API Token。
    第一次调用时不传 confirm=True 会返回确认信息，
    确认无误后第二次调用时传入 confirm=True 执行。
    
    参数:
        username: 具有管理员权限的Jenkins用户名
        api_token: Jenkins API Token
        confirm: 确认执行，必须为True才能执行
    
    返回:
        操作结果信息
    
    异常:
        PermissionError: 凭据无效或用户没有管理员权限
        ValueError: 未确认操作
    """
    cred_info = await verify_credentials(username, api_token)
    if cred_info["is_admin"] is False:
        raise PermissionError(
            f"用户 [{cred_info['user_id']}] 没有管理员权限，无法执行安全重启操作。\n"
            f"请使用具有管理员权限的 Jenkins 账户和 API Token。"
        )
    admin_status = "已验证 ✓" if cred_info["is_admin"] is True else "无法自动验证，将交由 Jenkins 鉴权"
    if not confirm:
        raise ValueError(
            f"⚠️  危险操作确认\n\n"
            f"操作: 安全重启 Jenkins\n"
            f"当前用户: {cred_info['user_id']} ({cred_info['full_name']})\n"
            f"管理员身份: {admin_status}\n\n"
            f"Jenkins 将等待所有运行中的构建完成后自动重启。\n"
            f"如确认执行，请传入参数 confirm=True"
        )
    jk = create_jenkins_client(username, api_token)
    jk.safe_restart()
    return {
        "success": True,
        "operation": "safe_restart",
        "message": "Jenkins 安全重启已触发，等待运行中的构建完成后将自动重启。",
        "triggered_by": cred_info["user_id"],
    }


@write_only
async def restart_jenkins(username: str, api_token: str, confirm: bool = False) -> dict:
    """强制重启Jenkins - 立即重启（会中断运行中的构建）
    
    需要提供具有管理员权限的Jenkins账户和API Token。
    第一次调用时不传 confirm=True 会返回确认信息，
    确认无误后第二次调用时传入 confirm=True 执行。
    
    参数:
        username: 具有管理员权限的Jenkins用户名
        api_token: Jenkins API Token
        confirm: 确认执行，必须为True才能执行
    
    返回:
        操作结果信息
    
    异常:
        PermissionError: 凭据无效或用户没有管理员权限
        ValueError: 未确认操作
    """
    cred_info = await verify_credentials(username, api_token)
    if cred_info["is_admin"] is False:
        raise PermissionError(
            f"用户 [{cred_info['user_id']}] 没有管理员权限，无法执行强制重启操作。\n"
            f"请使用具有管理员权限的 Jenkins 账户和 API Token。"
        )
    admin_status = "已验证 ✓" if cred_info["is_admin"] is True else "无法自动验证，将交由 Jenkins 鉴权"
    if not confirm:
        raise ValueError(
            f"⚠️  危险操作确认\n\n"
            f"操作: 强制重启 Jenkins\n"
            f"当前用户: {cred_info['user_id']} ({cred_info['full_name']})\n"
            f"管理员身份: {admin_status}\n\n"
            f"这将立即中断所有运行中的构建！\n"
            f"如确认执行，请传入参数 confirm=True"
        )
    jk = create_jenkins_client(username, api_token)
    jk.restart()
    return {
        "success": True,
        "operation": "restart",
        "message": "Jenkins 强制重启已触发，服务将立即重启。运行中的构建可能会被中断。",
        "triggered_by": cred_info["user_id"],
    }


@write_only
async def reload_jenkins_config(username: str, api_token: str, confirm: bool = False) -> dict:
    """重载Jenkins配置 - 从磁盘重新加载所有配置
    
    需要提供具有管理员权限的Jenkins账户和API Token。
    第一次调用时不传 confirm=True 会返回确认信息，
    确认无误后第二次调用时传入 confirm=True 执行。
    
    参数:
        username: 具有管理员权限的Jenkins用户名
        api_token: Jenkins API Token
        confirm: 确认执行，必须为True才能执行
    
    返回:
        操作结果信息
    
    异常:
        PermissionError: 凭据无效或用户没有管理员权限
        ValueError: 未确认操作
    """
    cred_info = await verify_credentials(username, api_token)
    if cred_info["is_admin"] is False:
        raise PermissionError(
            f"用户 [{cred_info['user_id']}] 没有管理员权限，无法执行重载配置操作。\n"
            f"请使用具有管理员权限的 Jenkins 账户和 API Token。"
        )
    admin_status = "已验证 ✓" if cred_info["is_admin"] is True else "无法自动验证，将交由 Jenkins 鉴权"
    if not confirm:
        raise ValueError(
            f"⚠️  危险操作确认\n\n"
            f"操作: 重载 Jenkins 配置\n"
            f"当前用户: {cred_info['user_id']} ({cred_info['full_name']})\n"
            f"管理员身份: {admin_status}\n\n"
            f"将重新加载磁盘上的所有 Jenkins 配置。\n"
            f"如确认执行，请传入参数 confirm=True"
        )
    jk = create_jenkins_client(username, api_token)
    jk.reload_configuration()
    return {
        "success": True,
        "operation": "reload_configuration",
        "message": "Jenkins 配置重载已触发，正在从磁盘重新加载配置。",
        "triggered_by": cred_info["user_id"],
    }


async def get_quiet_down_status(jk) -> dict:
    """检查Jenkins是否处于静默模式（quiet down）"""
    info = jk.get_info()
    is_quiet = info.get('quietDown', False)
    return {
        "quiet_down": is_quiet,
        "message": "Jenkins 当前处于静默模式（quiet down），不再接受新构建。" if is_quiet else "Jenkins 正常运行，未开启静默模式。",
    }


@write_only
async def quiet_down_jenkins(username: str, api_token: str, confirm: bool = False) -> dict:
    """设置Jenkins静默模式 - 不再接受新构建，等待运行中的构建完成后可安全重启

    需要提供具有管理员权限的Jenkins账户和API Token。
    第一次调用时不传 confirm=True 会返回确认信息，
    确认无误后第二次调用时传入 confirm=True 执行。
    """
    cred_info = await verify_credentials(username, api_token)
    if cred_info["is_admin"] is False:
        raise PermissionError(
            f"用户 [{cred_info['user_id']}] 没有管理员权限，无法设置静默模式。\n"
            f"请使用具有管理员权限的 Jenkins 账户和 API Token。"
        )
    admin_status = "已验证 ✓" if cred_info["is_admin"] is True else "无法自动验证，将交由 Jenkins 鉴权"
    if not confirm:
        raise ValueError(
            f"⚠️  危险操作确认\n\n"
            f"操作: 设置 Jenkins 静默模式（quiet down）\n"
            f"当前用户: {cred_info['user_id']} ({cred_info['full_name']})\n"
            f"管理员身份: {admin_status}\n\n"
            f"设置后 Jenkins 将不再接受新的构建请求。\n"
            f"如确认执行，请传入参数 confirm=True"
        )
    jk = create_jenkins_client(username, api_token)
    jk.quiet_down()
    return {
        "success": True,
        "operation": "quiet_down",
        "message": "Jenkins 静默模式已设置，不再接受新构建。",
        "triggered_by": cred_info["user_id"],
    }


@write_only
async def cancel_quiet_down_jenkins(username: str, api_token: str, confirm: bool = False) -> dict:
    """取消Jenkins静默模式 - 恢复正常接受构建

    需要提供具有管理员权限的Jenkins账户和API Token。
    第一次调用时不传 confirm=True 会返回确认信息，
    确认无误后第二次调用时传入 confirm=True 执行。
    """
    cred_info = await verify_credentials(username, api_token)
    if cred_info["is_admin"] is False:
        raise PermissionError(
            f"用户 [{cred_info['user_id']}] 没有管理员权限，无法取消静默模式。\n"
            f"请使用具有管理员权限的 Jenkins 账户和 API Token。"
        )
    admin_status = "已验证 ✓" if cred_info["is_admin"] is True else "无法自动验证，将交由 Jenkins 鉴权"
    if not confirm:
        raise ValueError(
            f"⚠️  危险操作确认\n\n"
            f"操作: 取消 Jenkins 静默模式（cancel quiet down）\n"
            f"当前用户: {cred_info['user_id']} ({cred_info['full_name']})\n"
            f"管理员身份: {admin_status}\n\n"
            f"取消后 Jenkins 将恢复正常接受新的构建请求。\n"
            f"如确认执行，请传入参数 confirm=True"
        )
    jk = create_jenkins_client(username, api_token)
    jk.cancel_quiet_down()
    return {
        "success": True,
        "operation": "cancel_quiet_down",
        "message": "Jenkins 静默模式已取消，恢复正常接受构建。",
        "triggered_by": cred_info["user_id"],
    }