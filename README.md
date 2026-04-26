# Jenkins MCP Server

基于 FastMCP 框架的 Jenkins 管理工具。

## 快速开始

### 1. 配置环境变量

复制 `.env.example` 为 `.env` 并填写配置：

```bash
cp jenkins_mcp/.env.example jenkins_mcp/.env
# 编辑 .env 文件，填写 JENKINS_URL、JENKINS_USERNAME、JENKINS_PASSWORD
```

### 2. 启动服务

```bash
# 设置 PYTHONPATH 并启动
set PYTHONPATH=jenkins_mcp\src
python -m jenkins_mcp.server

# 或直接运行
set PYTHONPATH=jenkins_mcp\src && python jenkins_mcp\src\jenkins_mcp\server.py
```

### 3. 可选：指定配置文件

```bash
set PYTHONPATH=jenkins_mcp\src
python -m jenkins_mcp.server --config jenkins_mcp\.env
```

## 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `-t, --transport` | 传输方式 (`stdio`, `sse`, `streamable-http`) | `stdio` |
| `-p, --port` | 本地监听端口 | `8000` |  
| `--host` | 本地监听地址 | `0.0.0.0` |
| `-c, --config` | .env配置文件路径 | `.env` |

## 环境变量 (.env文件)

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `JENKINS_URL` | Jenkins服务器地址 | `http://localhost:8080` |
| `JENKINS_USERNAME` | 用户名 | `admin` |
| `JENKINS_PASSWORD` | 密码或API Token | (空) |
| `JENKINS_TIMEOUT` | 超时时间(秒) | `30` |
| `JENKINS_VERIFY_SSL` | 是否验证SSL | `true` |
| `JENKINS_READ_ONLY` | 只读模式 | `false` |
| `MCP_TRANSPORT` | 传输方式 (`stdio`, `sse`, `streamable-http`) | `stdio` |
| `MCP_HOST` | 本地监听地址 | `0.0.0.0` |
| `MCP_PORT` | 本地监听端口 | `8000` |

## MCP 工具列表

### Job管理 (12个)
- `get_all_jobs` - 获取所有Job
- `get_job` - 获取Job详情
- `get_job_config` - 获取Job配置
- `set_job_config` - 设置Job配置
- `create_job` - 创建Job
- `delete_job` - 删除Job
- `copy_job` - 复制Job
- `enable_job` - 启用Job
- `disable_job` - 禁用Job
- `build_job` - 触发构建

### Build管理 (5个)
- `get_build` - 获取Build信息
- `get_build_console_output` - 获取构建日志
- `get_running_builds` - 获取运行中的Build
- `stop_build` - 停止Build
- `delete_build` - 删除Build

### Queue管理 (5个)
- `get_all_queue_items` - 获取所有队列项
- `get_queue_item` - 获取队列项详情
- `get_queue_items_by_job` - 获取Job的队列项
- `cancel_queue_item` - 取消队列项
- `cancel_job_queue` - 取消Job队列
- `cancel_all_queue` - 取消所有队列

### Node管理 (8个)
- `get_all_nodes` - 获取所有节点
- `get_node` - 获取节点详情
- `get_node_config` - 获取节点配置
- `set_node_config` - 设置节点配置
- `create_node` - 创建节点
- `delete_node` - 删除节点
- `set_node_offline` - 设置节点离线
- `set_node_online` - 设置节点在线

### Plugin管理 (3个)
- `get_all_plugins` - 获取所有插件
- `get_plugin` - 获取插件详情
- `get_plugins_with_problems` - 获取有问题的插件

## 权限控制

设置 `JENKINS_READ_ONLY=true` 启用只读模式，阻止所有写操作。