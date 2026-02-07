#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地存储模块
Local Storage Module

管理历史记录和用户偏好
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Optional, Any


class LocalStorage:
    """本地存储管理器"""
    
    def __init__(self, data_dir: Optional[str] = None):
        """
        初始化存储管理器
        
        Args:
            data_dir: 数据目录路径，默认为当前目录下的data/
        """
        if data_dir is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.data_dir = os.path.join(base_dir, 'data')
        else:
            self.data_dir = data_dir
        
        self.history_file = os.path.join(self.data_dir, 'history.json')
        self.user_prefs_file = os.path.join(self.data_dir, 'user_prefs.json')
        
        # 确保目录存在
        self._ensure_data_dir()
    
    def _ensure_data_dir(self):
        """确保数据目录存在"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir, exist_ok=True)
    
    def save_copy(self, copy_data: Dict) -> str:
        """
        保存生成的文案
        
        Args:
            copy_data: 文案数据
        
        Returns:
            唯一ID
        """
        # 生成唯一ID
        copy_id = f"copy_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 添加元数据
        record = {
            "id": copy_id,
            "title": copy_data.get('title', ''),
            "body": copy_data.get('full_content', copy_data.get('body', '')),
            "industry": copy_data.get('industry', ''),
            "hashtags": copy_data.get('hashtags', []),
            "formula_used": copy_data.get('formula_used', ''),
            "score": copy_data.get('score', 0),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # 读取现有历史
        history = self._load_history()
        
        # 添加新记录
        history.append(record)
        
        # 限制历史记录数量（保留最近100条）
        max_history = 100
        if len(history) > max_history:
            history = history[-max_history:]
        
        # 保存
        self._save_history(history)
        
        return copy_id
    
    def _load_history(self) -> List[Dict]:
        """加载历史记录"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"⚠️  加载历史记录失败: {e}")
        return []
    
    def _save_history(self, history: List[Dict]):
        """保存历史记录"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️  保存历史记录失败: {e}")
    
    def get_history(self, limit: int = 20, industry: Optional[str] = None) -> List[Dict]:
        """
        获取历史记录
        
        Args:
            limit: 返回最近N条
            industry: 筛选特定行业（可选）
        
        Returns:
            历史记录列表
        """
        history = self._load_history()
        
        # 按行业过滤
        if industry:
            history = [h for h in history if h.get('industry') == industry]
        
        # 按时间倒序排序
        history.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        # 返回前N条
        return history[:limit]
    
    def get_copy_by_id(self, copy_id: str) -> Optional[Dict]:
        """
        根据ID获取文案详情
        
        Args:
            copy_id: 文案ID
        
        Returns:
            文案数据或None
        """
        history = self._load_history()
        for record in history:
            if record.get('id') == copy_id:
                return record
        return None
    
    def delete_copy(self, copy_id: str) -> bool:
        """
        删除指定文案
        
        Args:
            copy_id: 文案ID
        
        Returns:
            是否成功删除
        """
        history = self._load_history()
        original_len = len(history)
        history = [h for h in history if h.get('id') != copy_id]
        
        if len(history) < original_len:
            self._save_history(history)
            return True
        return False
    
    def update_prefs(self, prefs: Dict):
        """
        更新用户偏好设置
        
        Args:
            prefs: 偏好设置
        """
        try:
            existing_prefs = self.get_prefs()
            existing_prefs.update(prefs)
            existing_prefs['updated_at'] = datetime.now().isoformat()
            
            with open(self.user_prefs_file, 'w', encoding='utf-8') as f:
                json.dump(existing_prefs, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️  保存偏好设置失败: {e}")
    
    def get_prefs(self) -> Dict:
        """
        获取用户偏好设置
        
        Returns:
            偏好设置
        """
        default_prefs = {
            "default_industry": "beauty",
            "emoji_style": "moderate",
            "language": "zh",
            "auto_save": True,
            "max_history": 100,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        try:
            if os.path.exists(self.user_prefs_file):
                with open(self.user_prefs_file, 'r', encoding='utf-8') as f:
                    prefs = json.load(f)
                    # 合并默认值
                    for key, value in default_prefs.items():
                        if key not in prefs:
                            prefs[key] = value
                    return prefs
        except Exception as e:
            print(f"⚠️  加载偏好设置失败: {e}")
        
        return default_prefs
    
    def generate_variation(self, old_copy: Dict) -> Dict:
        """
        基于历史文案生成变体
        
        Args:
            old_copy: 旧文案数据
        
        Returns:
            新文案数据
        """
        import random
        
        # 简单的变体生成逻辑
        title = old_copy.get('title', '')
        
        # 添加变体标记
        variations = [
            "【升级版】",
            "【2.0版】",
            "【补充版】",
            "【详细版】",
        ]
        
        new_title = f"{random.choice(variations)}{title}"
        
        # 复制其他数据
        new_copy = old_copy.copy()
        new_copy['title'] = new_title
        new_copy['id'] = f"copy_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        new_copy['created_at'] = datetime.now().isoformat()
        new_copy['updated_at'] = datetime.now().isoformat()
        new_copy['is_variation'] = True
        new_copy['original_id'] = old_copy.get('id')
        
        return new_copy


# 便捷函数
def save_copy(copy_data: Dict) -> str:
    """便捷函数：保存文案"""
    storage = LocalStorage()
    return storage.save_copy(copy_data)


def get_history(limit: int = 20, industry: Optional[str] = None) -> List[Dict]:
    """便捷函数：获取历史"""
    storage = LocalStorage()
    return storage.get_history(limit, industry)


def get_copy_by_id(copy_id: str) -> Optional[Dict]:
    """便捷函数：获取文案"""
    storage = LocalStorage()
    return storage.get_copy_by_id(copy_id)


def delete_copy(copy_id: str) -> bool:
    """便捷函数：删除文案"""
    storage = LocalStorage()
    return storage.delete_copy(copy_id)


def update_prefs(prefs: Dict):
    """便捷函数：更新偏好"""
    storage = LocalStorage()
    storage.update_prefs(prefs)


def get_prefs() -> Dict:
    """便捷函数：获取偏好"""
    storage = LocalStorage()
    return storage.get_prefs()


if __name__ == '__main__':
    # 测试
    print("💾 本地存储测试")
    print("-" * 50)
    
    storage = LocalStorage()
    
    # 测试保存
    test_copy = {
        "title": "测试文案",
        "full_content": "这是测试内容",
        "industry": "beauty",
        "hashtags": ["#测试"],
        "formula_used": "test",
        "score": 80
    }
    
    copy_id = storage.save_copy(test_copy)
    print(f"✓ 保存成功，ID: {copy_id}")
    
    # 测试读取
    history = storage.get_history(limit=1)
    print(f"✓ 历史记录数: {len(history)}")
    
    # 测试偏好
    storage.update_prefs({"default_industry": "fashion"})
    prefs = storage.get_prefs()
    print(f"✓ 默认行业: {prefs['default_industry']}")
    
    print("\n✅ 所有测试通过！")
