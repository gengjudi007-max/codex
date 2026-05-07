#!/usr/bin/env python3
"""
持久化任务队列
使用 JSON 文件存储任务状态，支持任务的创建、执行、完成和失败重试
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional


class TaskQueue:
    """持久化任务队列"""
    
    def __init__(self, queue_file: str = "data/task_queue.json"):
        self.queue_file = queue_file
        self._ensure_queue_file()
    
    def _ensure_queue_file(self):
        """确保队列文件存在"""
        os.makedirs(os.path.dirname(self.queue_file), exist_ok=True)
        if not os.path.exists(self.queue_file):
            self._save_tasks([])
    
    def _load_tasks(self) -> List[Dict[str, Any]]:
        """加载所有任务"""
        try:
            with open(self.queue_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ 加载任务队列失败：{e}")
            return []
    
    def _save_tasks(self, tasks: List[Dict[str, Any]]):
        """保存所有任务"""
        try:
            with open(self.queue_file, 'w', encoding='utf-8') as f:
                json.dump(tasks, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"❌ 保存任务队列失败：{e}")
    
    def add_task(self, task_type: str, data: Dict[str, Any], priority: int = 5) -> str:
        """
        添加任务到队列
        
        Args:
            task_type: 任务类型（如 'collect_data', 'generate_topic', 'generate_draft'）
            data: 任务数据
            priority: 优先级（1-10，数字越大优先级越高）
        
        Returns:
            任务 ID
        """
        tasks = self._load_tasks()
        
        task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(tasks)}"
        
        task = {
            'id': task_id,
            'type': task_type,
            'data': data,
            'priority': priority,
            'status': 'pending',  # pending, running, completed, failed
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'result': None,
            'error': None,
            'retry_count': 0,
            'max_retries': 3
        }
        
        tasks.append(task)
        self._save_tasks(tasks)
        
        print(f"✅ 任务已添加：{task_id}（类型：{task_type}）")
        return task_id
    
    def get_next_task(self) -> Optional[Dict[str, Any]]:
        """
        获取下一个待执行的任务（按优先级排序）
        
        Returns:
            任务字典，如果没有待执行任务则返回 None
        """
        tasks = self._load_tasks()
        
        # 筛选出待执行的任务
        pending_tasks = [t for t in tasks if t['status'] == 'pending']
        
        if not pending_tasks:
            return None
        
        # 按优先级排序（数字越大优先级越高）
        pending_tasks.sort(key=lambda x: x['priority'], reverse=True)
        
        return pending_tasks[0]
    
    def update_task_status(self, task_id: str, status: str, result: Any = None, error: str = None):
        """
        更新任务状态
        
        Args:
            task_id: 任务 ID
            status: 新状态（'running', 'completed', 'failed'）
            result: 任务结果（可选）
            error: 错误信息（可选）
        """
        tasks = self._load_tasks()
        
        for task in tasks:
            if task['id'] == task_id:
                task['status'] = status
                task['updated_at'] = datetime.now().isoformat()
                
                if result is not None:
                    task['result'] = result
                
                if error is not None:
                    task['error'] = error
                
                self._save_tasks(tasks)
                print(f"✅ 任务状态已更新：{task_id} → {status}")
                return
        
        print(f"⚠️  未找到任务：{task_id}")
    
    def retry_task(self, task_id: str) -> bool:
        """
        重试失败的任务
        
        Args:
            task_id: 任务 ID
        
        Returns:
            是否成功标记为重试状态
        """
        tasks = self._load_tasks()
        
        for task in tasks:
            if task['id'] == task_id:
                if task['status'] != 'failed':
                    print(f"⚠️  任务 {task_id} 不是失败状态，无法重试")
                    return False
                
                if task['retry_count'] >= task['max_retries']:
                    print(f"⚠️  任务 {task_id} 已达到最大重试次数")
                    return False
                
                task['status'] = 'pending'
                task['retry_count'] += 1
                task['updated_at'] = datetime.now().isoformat()
                
                self._save_tasks(tasks)
                print(f"✅ 任务已标记为重试：{task_id}（第 {task['retry_count']} 次重试）")
                return True
        
        print(f"⚠️  未找到任务：{task_id}")
        return False
    
    def get_task_stats(self) -> Dict[str, int]:
        """
        获取任务统计信息
        
        Returns:
            包含各种状态任务数量的字典
        """
        tasks = self._load_tasks()
        
        stats = {
            'total': len(tasks),
            'pending': len([t for t in tasks if t['status'] == 'pending']),
            'running': len([t for t in tasks if t['status'] == 'running']),
            'completed': len([t for t in tasks if t['status'] == 'completed']),
            'failed': len([t for t in tasks if t['status'] == 'failed'])
        }
        
        return stats
    
    def list_tasks(self, status: str = None) -> List[Dict[str, Any]]:
        """
        列出所有任务
        
        Args:
            status: 可选，按状态筛选（'pending', 'running', 'completed', 'failed'）
        
        Returns:
            任务列表
        """
        tasks = self._load_tasks()
        
        if status:
            tasks = [t for t in tasks if t['status'] == status]
        
        return tasks


# 使用示例
if __name__ == '__main__':
    # 创建任务队列
    queue = TaskQueue()
    
    # 添加任务
    queue.add_task('collect_data', {'city': '北京', 'source': 'land'})
    queue.add_task('generate_topic', {'items': []}, priority=8)
    queue.add_task('generate_draft', {'topic': '测试选题'}, priority=10)
    
    # 查看统计
    stats = queue.get_task_stats()
    print(f"\n📊 任务统计：{stats}")
    
    # 列出所有待执行任务
    next_task = queue.get_next_task()
    if next_task:
        print(f"\n📝 下一个任务：{next_task['id']}（优先级：{next_task['priority']}）")
    
    # 更新任务状态
    if next_task:
        queue.update_task_status(next_task['id'], 'running')
        # 模拟任务执行
        queue.update_task_status(next_task['id'], 'completed', result={'output': '成功'})
    
    # 列出所有任务
    print(f"\n📋 所有任务：")
    for task in queue.list_tasks():
        print(f"  - {task['id']}: {task['status']} (优先级: {task['priority']})")
