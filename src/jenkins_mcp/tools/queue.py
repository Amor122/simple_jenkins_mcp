"""
Jenkins MCP Server - Queue管理工具模块

基于python-jenkins的实现
"""

from jenkins_mcp.tools.utils import check_read_only


# ==================== Queue管理工具 ====================

async def get_all_queue_items(jk) -> list:
    """
    获取队列中所有项目
    
    返回:
        队列项列表
    """
    check_read_only({'read'})
    return jk.get_queue_info()


async def get_queue_item(jk, id: int, depth: int = 0) -> dict:
    """
    获取队列项详情
    
    参数:
        id: 队列ID
        depth: JSON深度
    
    返回:
        队列项详情
    """
    check_read_only({'read'})
    return jk.get_queue_item(id, depth)


async def get_queue_items_by_job(jk, name: str) -> list:
    """
    获取指定Job的队列项
    
    参数:
        name: Job名称
    
    返回:
        队列项列表
    """
    check_read_only({'read'})
    queue_info = jk.get_queue_info()
    return [item for item in queue_info if item.get('task', {}).get('name') == name]


async def cancel_queue_item(jk, id: int) -> dict:
    """
    取消队列项
    
    参数:
        id: 队列ID
    
    返回:
        执行结果
    """
    check_read_only({'write'})
    jk.cancel_queue(id)
    return {"status": "cancelled", "queue_id": id}


async def cancel_job_queue(jk, name: str) -> dict:
    """
    取消指定Job的所有队列项
    
    参数:
        name: Job名称
    
    返回:
        取消的队列项列表
    """
    check_read_only({'write'})
    queue_info = jk.get_queue_info()
    cancelled = []
    
    for item in queue_info:
        if item.get('task', {}).get('name') == name:
            item_id = item.get('id')
            if item_id:
                jk.cancel_queue(item_id)
                cancelled.append(item_id)
    
    return {"status": "cancelled", "job": name, "count": len(cancelled)}


async def cancel_all_queue(jk) -> dict:
    """
    取消所有队列项
    
    返回:
        取消的队列项列表
    """
    check_read_only({'write'})
    queue_info = jk.get_queue_info()
    cancelled = []
    
    for item in queue_info:
        item_id = item.get('id')
        if item_id:
            jk.cancel_queue(item_id)
            cancelled.append(item_id)
    
    return {"status": "cancelled", "total": len(cancelled)}