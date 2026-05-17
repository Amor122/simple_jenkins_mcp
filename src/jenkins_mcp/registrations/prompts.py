"""Jenkins 提示模板注册 - 可复用的操作向导

Prompt 列表:
  debug-build(job, build)       诊断构建失败：自动获取状态、日志尾部、环境变量
  compare-builds(job, b1, b2)   对比两次构建：环境变量差异
  safe-restart                  安全重启向导：静默 → 检查 → 重启
"""

from mcp.server.fastmcp import FastMCP


def register_prompts(mcp: FastMCP) -> None:
    """注册提示模板"""

    def get_jk():
        from jenkins_mcp.server import get_jenkins_client
        return get_jenkins_client()

    @mcp.prompt()
    async def debug_build(job: str, build: int) -> str:
        """诊断构建失败：获取构建状态、日志尾部（最后50行）、环境变量概览"""
        jk = get_jk()
        result = jk.get_build_info(job, build)
        status = result.get('result', 'UNKNOWN')
        console = jk.get_build_console_output(job, build)
        tail = "\n".join(console.split("\n")[-50:]) if console else "(空)"
        try:
            env = jk.get_build_env_vars(job, build)
            env_summary = "\n".join(f"  {k}={v}" for k, v in list(env.items())[:20])
            if len(env) > 20:
                env_summary += f"\n  ... 共 {len(env)} 个变量"
        except Exception:
            env_summary = "(无法获取)"

        return f"""## Build 诊断报告: {job} #{build}

### 状态
- 结果: {status}

### 环境变量概览（前 20 个）
{env_summary}

### 日志尾部（最后 50 行）
```
{tail}
```

### 建议的后续操作
1. 使用 `get_build_env_vars` 查看完整环境变量
2. 使用 `get_build_console_output` 查看完整日志
3. 使用 `get_build_artifacts` 查看构建制品"""

    @mcp.prompt()
    async def compare_builds(job: str, build1: int, build2: int) -> str:
        """对比两次构建的环境变量差异"""
        jk = get_jk()
        try:
            vars1 = jk.get_build_env_vars(job, build1)
            vars2 = jk.get_build_env_vars(job, build2)
        except Exception as e:
            return f"获取环境变量失败: {e}"

        keys1, keys2 = set(vars1.keys()), set(vars2.keys())
        added = keys2 - keys1
        removed = keys1 - keys2
        changed = {k for k in (keys1 & keys2) if vars1[k] != vars2[k]}

        lines = [f"## 环境变量对比: {job} #{build1} vs #{build2}", ""]
        lines.append(f"- Build #{build1}: {len(vars1)} 个变量")
        lines.append(f"- Build #{build2}: {len(vars2)} 个变量")
        lines.append(f"- 新增: {len(added)} | 移除: {len(removed)} | 变化: {len(changed)}")
        lines.append("")

        if added:
            lines.append("### 新增变量")
            for k in sorted(added):
                lines.append(f"  + {k} = {vars2[k]}")
            lines.append("")

        if removed:
            lines.append("### 移除变量")
            for k in sorted(removed):
                lines.append(f"  - {k} = {vars1[k]}")
            lines.append("")

        if changed:
            lines.append("### 值变化")
            for k in sorted(changed):
                lines.append(f"  ~ {k}: {vars1[k]} → {vars2[k]}")
            lines.append("")

        return "\n".join(lines)

    @mcp.prompt()
    async def safe_restart() -> str:
        """Jenkins 安全重启向导"""
        return """## Jenkins 安全重启步骤

### 步骤 1: 检查当前状态
- 使用 `get_quiet_down_status` 确认 Jenkins 当前模式
- 使用 `get_running_builds` 检查是否有运行中的构建

### 步骤 2: 设置静默模式
- 使用 `quiet_down_jenkins` 停止接受新构建
  - 需要管理员账户 + API Token
  - 首次调用返回确认信息，传入 `confirm=True` 执行

### 步骤 3: 等待构建完成
- 使用 `get_running_builds` 确认所有构建已完成
- 使用 `get_all_queue_items` 确认队列为空

### 步骤 4: 执行安全重启
- 使用 `safe_restart_jenkins` 触发安全重启
  - 需要管理员账户 + API Token
  - 首次调用返回确认信息，传入 `confirm=True` 执行

### 步骤 5: 验证恢复
- 重启后使用 `get_jenkins_version` 确认 Jenkins 已上线
- 使用 `cancel_quiet_down_jenkins` 恢复正常模式"""
