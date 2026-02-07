#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
热点匹配算法模块
Hot Topic Matcher Module
"""

import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime

class HotTopicMatcher:
    """热点匹配器 - 基于用户输入匹配最相关的热点"""
    
    def __init__(self, builtin_path: str):
        """
        初始化热点匹配器
        
        Args:
            builtin_path: 内置热点库JSON文件路径
        """
        self.builtin_path = builtin_path
        self.builtin = self._load_builtin()
    
    def _load_builtin(self) -> Dict:
        """加载内置热点库"""
        try:
            with open(self.builtin_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  加载热点库失败: {e}")
            return {"categories": {}}
    
    def match(self, user_input: str, industry: str, top_k: int = 5) -> List[Dict]:
        """
        基于用户输入和行业，匹配最相关的热点
        
        Args:
            user_input: 用户输入的产品/主题（如"春季防晒霜"）
            industry: 行业ID
            top_k: 返回前K个匹配结果
        
        Returns:
            匹配的热点列表，按相关度排序
        """
        results = []
        text = self._normalize_text(user_input)
        
        # 遍历所有热点
        for category_id, category in self.builtin.get("categories", {}).items():
            for topic in category.get("topics", []):
                # 检查行业匹配
                suitable = self._normalize_suitable_industries(topic.get("suitable_industries", []))
                if industry not in suitable:
                    continue
                
                # 检查时效性
                if not self._is_active(topic):
                    continue
                
                # 计算相关度（中文友好：关键词子串命中）
                matched, relevance_score = self._calculate_relevance(text, topic.get("keywords", []), topic.get("heat", 50))
                
                if relevance_score > 0:
                    results.append({
                        "topic": topic,
                        "relevance_score": relevance_score,
                        "matched_keywords": matched,
                        "suggested_angle": topic.get("angles", [""])[0] if topic.get("angles") else ""
                    })
        
        # 按相关度排序
        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        return results[:top_k]
    
    def _normalize_text(self, text: str) -> str:
        return (text or "").strip().lower()

    def _normalize_suitable_industries(self, industries: Any) -> List[str]:
        if not industries:
            return []

        if not isinstance(industries, list):
            return []

        alias = {
            "skincare": "beauty",
            "health": "fitness",
            "lifestyle": "home",
            "entertainment": "fashion",
        }
        out: List[str] = []
        for v in industries:
            s = str(v).strip().lower()
            if not s:
                continue
            out.append(alias.get(s, s))
        return out
    
    def _is_active(self, topic: Dict) -> bool:
        """检查热点是否在有效期内"""
        try:
            today = datetime.now()
            start_date = datetime.strptime(topic.get("start_date", "2000-01-01"), "%Y-%m-%d")
            end_date = datetime.strptime(topic.get("end_date", "2099-12-31"), "%Y-%m-%d")
            return start_date <= today <= end_date
        except:
            return True
    
    def _calculate_relevance(self, text: str, topic_keywords: List[str], heat: int) -> Any:
        if not text or not topic_keywords:
            return [], 0.0

        matched: List[str] = []
        for kw in topic_keywords:
            k = str(kw).strip().lower()
            if not k:
                continue
            if k in text:
                matched.append(str(kw))

        if not matched:
            return [], 0.0

        base = min(70.0, len(matched) * 22.0)
        heat_bonus = (float(heat) / 100.0) * 30.0
        score = min(base + heat_bonus, 100.0)
        return matched[:8], score
    
    def get_angles(self, topic_id: str) -> List[str]:
        """获取指定热点的借势角度建议"""
        for category in self.builtin.get("categories", {}).values():
            for topic in category.get("topics", []):
                if topic.get("id") == topic_id:
                    return topic.get("angles", [])
        return []
    
    def get_all_categories(self) -> List[Dict]:
        """获取所有热点类别"""
        categories = []
        for cat_id, cat_data in self.builtin.get("categories", {}).items():
            categories.append({
                "id": cat_id,
                "name": cat_data.get("name", ""),
                "icon": cat_data.get("icon", "")
            })
        return categories
    
    def get_topics_by_category(self, category_id: str) -> List[Dict]:
        """获取指定类别的所有热点"""
        category = self.builtin.get("categories", {}).get(category_id, {})
        return category.get("topics", [])


# 便捷函数
def match_hot_topics(user_input: str, industry: str, top_k: int = 5) -> List[Dict]:
    """
    便捷函数：匹配热点
    
    Args:
        user_input: 用户输入
        industry: 行业ID
        top_k: 返回数量
    
    Returns:
        匹配的热点列表
    """
    # 获取当前文件所在目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    builtin_path = os.path.join(current_dir, 'builtin.json')
    
    matcher = HotTopicMatcher(builtin_path)
    return matcher.match(user_input, industry, top_k)


if __name__ == '__main__':
    # 测试
    print("🔥 热点匹配器测试")
    print("-" * 50)
    
    # 测试匹配
    results = match_hot_topics("春季防晒霜", "beauty", top_k=3)
    
    if results:
        print(f"\n找到 {len(results)} 个相关热点:\n")
        for i, result in enumerate(results, 1):
            topic = result["topic"]
            print(f"{i}. {topic['name']} (热度: {topic['heat']})")
            print(f"   相关度: {result['relevance_score']:.1f}/100")
            print(f"   匹配词: {', '.join(result['matched_keywords'])}")
            print(f"   推荐角度: {result['suggested_angle']}")
            print()
    else:
        print("未找到相关热点")
