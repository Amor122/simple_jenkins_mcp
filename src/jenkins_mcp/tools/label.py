"""
Jenkins MCP Server - Label管理工具模块

基于python-jenkins的实现
"""

from jenkins_mcp.tools.utils import check_read_only


def _parse_labels_from_node(node_info: dict) -> list:
    """从节点信息中解析出label列表"""
    labels = []
    assigned_labels = node_info.get('assignedLabels', [])
    
    for label_data in assigned_labels:
        if isinstance(label_data, dict):
            label_name = label_data.get('name', '')
            if label_name:
                labels.append(label_name)
        elif label_data:
            labels.append(str(label_data))
    
    return labels


from jenkins_mcp.jenkins import JenkinsException


async def get_all_labels(jk, depth: int = 2) -> list:
    """获取所有Label及其关联的节点
    
    通过nodes API获取每个label关联的节点信息
    
    参数:
        jk: Jenkins客户端
        depth: API深度
    
    返回:
        Label列表，每个label包含名称和关联的节点
    """
    check_read_only({'read'})
    nodes_data = jk.get_nodes(depth=depth)
    
    labels_dict = {}
    
    for node in nodes_data:
        node_name = node.get('displayName', node.get('name', ''))
        
        if node_name == 'Built-In Node':
            node_name_for_api = '(master)'
        else:
            node_name_for_api = node_name
        
        node_info = jk.get_node_info(node_name_for_api, depth=depth)
        node_labels = _parse_labels_from_node(node_info)
        
        for label_name in node_labels:
            if label_name not in labels_dict:
                labels_dict[label_name] = {
                    'name': label_name,
                    'nodes': [],
                    'jobs': []
                }
            
            labels_dict[label_name]['nodes'].append({
                'name': node_name,
                'offline': node_info.get('offline', False),
                'numExecutors': node_info.get('numExecutors', 0)
            })
            
            for job in node_info.get('tiedJobs', []):
                if job.get('name') not in labels_dict[label_name]['jobs']:
                    labels_dict[label_name]['jobs'].append(job.get('name', ''))
    
    return list(labels_dict.values())


async def get_label(jk, name: str, depth: int = 2) -> dict:
    """获取指定Label的详细信息
    
    参数:
        jk: Jenkins客户端
        name: Label名称
        depth: API深度
    
    返回:
        Label详情
    """
    check_read_only({'read'})
    
    nodes_data = jk.get_nodes(depth=depth)
    
    label_info = {
        'name': name,
        'nodes': [],
        'jobs': []
    }
    
    for node in nodes_data:
        node_name = node.get('displayName', node.get('name', ''))
        
        if node_name == 'Built-In Node':
            node_name_for_api = '(master)'
        else:
            node_name_for_api = node_name
        
        node_info = jk.get_node_info(node_name_for_api, depth=depth)
        node_labels = _parse_labels_from_node(node_info)
        
        if name in node_labels:
            label_info['nodes'].append({
                'name': node_name,
                'offline': node_info.get('offline', False),
                'numExecutors': node_info.get('numExecutors', 0),
                'architecture': node_info.get('architecture', 'unknown')
            })
            
            for job in node_info.get('tiedJobs', []):
                if job.get('name') not in label_info['jobs']:
                    label_info['jobs'].append(job.get('name', ''))
    
    return label_info


async def get_nodes_by_label(jk, label: str, depth: int = 2) -> list:
    """获取具有指定Label的所有节点
    
    参数:
        jk: Jenkins客户端
        label: Label名称
        depth: API深度
    
    返回:
        节点列表
    """
    check_read_only({'read'})
    
    nodes_data = jk.get_nodes(depth=depth)
    result = []
    
    for node in nodes_data:
        node_name = node.get('displayName', node.get('name', ''))
        
        if node_name == 'Built-In Node':
            node_name_for_api = '(master)'
        else:
            node_name_for_api = node_name
        
        node_info = jk.get_node_info(node_name_for_api, depth=depth)
        node_labels = _parse_labels_from_node(node_info)
        
        if label in node_labels:
            result.append({
                'name': node_name,
                'offline': node_info.get('offline', False),
                'numExecutors': node_info.get('numExecutors', 0),
                'labels': node_labels
            })
    
    return result


async def get_label_load(jk) -> dict:
    """获取Label负载信息
    
    获取整体负载统计和各Label的使用情况
    
    返回:
        负载信息
    """
    check_read_only({'read'})
    
    try:
        info = jk.get_info()
        return {
            'busyExecutors': info.get('busyExecutors', 0),
            'totalExecutors': info.get('totalExecutors', 0),
            'queueLength': info.get('queueLength', 0)
        }
    except Exception as e:
        raise JenkinsException(f'Failed to get label load: {e}')