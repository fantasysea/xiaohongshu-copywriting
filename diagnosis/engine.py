#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文案诊断引擎
Copy Diagnosis Engine

提供5维度文案质量分析
"""

import json
import os
import re
from typing import Dict, List, Optional, Any


class CopyDiagnosis:
    """文案诊断器 - 5维度质量分析"""
    
    def __init__(self, industries_dir: str, formulas_dir: str, diagnosis_dir: str):
        """
        初始化诊断器
        
        Args:
            industries_dir: 行业配置目录
            formulas_dir: 标题公式目录
            diagnosis_dir: 诊断模块目录
        """
        self.industries_dir = industries_dir
        self.formulas_dir = formulas_dir
        self.diagnosis_dir = diagnosis_dir
        self.sensitive_words = self._load_sensitive_words()
    
    def _load_sensitive_words(self) -> Dict:
        """加载敏感词库"""
        try:
            filepath = os.path.join(self.diagnosis_dir, 'sensitive_words.json')
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  加载敏感词库失败: {e}")
            return {}
    
    def diagnose(self, title: str, body: str, industry_id: str) -> Dict:
        """
        5维度文案诊断
        
        Args:
            title: 标题
            body: 正文
            industry_id: 行业ID
        
        Returns:
            诊断报告
        """
        full_text = title + " " + body
        
        dimensions = {
            "click_rate": self._analyze_click_rate(title, industry_id),
            "completion_rate": self._analyze_completion(body),
            "conversion": self._analyze_conversion(body),
            "compliance": self._analyze_compliance(full_text),
            "seo": self._analyze_seo(full_text, industry_id)
        }
        
        # 计算总分
        overall_score = sum(d['score'] for d in dimensions.values()) // len(dimensions)
        
        return {
            "overall_score": overall_score,
            "dimensions": dimensions,
            "improved_version": self._generate_improved_version(title, body, dimensions)
        }
    
    def _analyze_click_rate(self, title: str, industry_id: str) -> Dict:
        """点击率分析"""
        score = 70
        suggestions = []
        
        # 检查标题长度
        if len(title) <= 20:
            score += 10
        else:
            suggestions.append("标题建议控制在20字以内，避免被截断")
        
        # 检查是否包含emoji
        if any(ord(c) > 127 for c in title):
            score += 10
        else:
            suggestions.append("建议添加emoji增强视觉吸引力")
        
        # 检查是否包含数字
        if any(c.isdigit() for c in title):
            score += 5
        
        # 检查是否包含情绪化词汇
        emotion_words = ['绝', '必', '神', 'yyds', '封神', '绝了']
        if any(w in title for w in emotion_words):
            score += 5
        else:
            suggestions.append("可以尝试加入情绪化词汇提升点击欲")
        
        return {
            "score": min(score, 100),
            "analysis": f"标题长度{len(title)}字，{'符合' if len(title) <= 20 else '超出'}推荐范围",
            "suggestions": suggestions if suggestions else ["标题吸引力良好，可尝试A/B测试不同版本"]
        }
    
    def _analyze_completion(self, body: str) -> Dict:
        """完读率分析"""
        score = 65
        suggestions = []
        
        # 检查开头
        if body.startswith(('姐妹们', '家人们', '宝子们', '哈喽')):
            score += 10
        else:
            suggestions.append("开头建议用亲切的称呼拉近距离")
        
        # 检查段落数
        paragraphs = [p for p in body.split('\n\n') if p.strip()]
        if 3 <= len(paragraphs) <= 6:
            score += 10
        elif len(paragraphs) < 3:
            suggestions.append("正文建议分3-6段，当前段落数偏少")
        else:
            suggestions.append("段落数较多，建议精简内容")
        
        # 检查emoji使用
        emoji_count = sum(1 for c in body if ord(c) > 127)
        if emoji_count >= 3:
            score += 10
        else:
            suggestions.append("建议增加emoji使用，提升阅读体验")
        
        # 检查是否有钩子
        hook_words = ['秘密', '秘诀', '技巧', '方法', '攻略', '必看']
        if any(w in body for w in hook_words):
            score += 5
        else:
            suggestions.append("正文建议包含具体的技巧或方法")
        
        return {
            "score": min(score, 100),
            "analysis": f"正文共{len(paragraphs)}段，emoji使用{emoji_count}个",
            "suggestions": suggestions if suggestions else ["正文结构良好，信息密度适中"]
        }
    
    def _analyze_conversion(self, body: str) -> Dict:
        """转化力分析"""
        score = 60
        suggestions = []
        
        # 检查CTA
        cta_words = ['点赞', '收藏', '关注', '评论', '转发', '私信']
        has_cta = any(w in body for w in cta_words)
        if has_cta:
            score += 15
        else:
            suggestions.append("结尾添加明确的行动号召（点赞/收藏/关注）")
        
        # 检查信任背书
        trust_words = ['亲测', '真实', '实测', '自用', '回购', '推荐']
        if any(w in body for w in trust_words):
            score += 10
        else:
            suggestions.append("可以加入信任背书（亲测/真实体验）")
        
        # 检查福利承诺
        benefit_words = ['送', '福利', '免费', '分享', '整理']
        if any(w in body for w in benefit_words):
            score += 10
        else:
            suggestions.append("可以加入福利承诺提升转化")
        
        # 检查紧迫感
        urgency_words = ['限时', '快', '赶紧', '马上', '立即']
        if any(w in body for w in urgency_words):
            score += 5
        
        return {
            "score": min(score, 100),
            "analysis": f"{'有' if has_cta else '无'}明确CTA，转化引导{'良好' if score > 70 else '需加强'}",
            "suggestions": suggestions if suggestions else ["转化引导较好，可测试不同CTA效果"]
        }
    
    def _analyze_compliance(self, text: str) -> Dict:
        """合规检查"""
        score = 95
        warnings = []
        
        # 检查极限词
        extreme_words = self.sensitive_words.get('extreme_words', [])
        found_extreme = [w for w in extreme_words if w in text]
        if found_extreme:
            score -= len(found_extreme) * 10
            warnings.append(f"发现极限词: {', '.join(found_extreme[:3])}")
        
        # 检查医疗宣称
        medical_words = self.sensitive_words.get('medical_claims', [])
        found_medical = [w for w in medical_words if w in text]
        if found_medical:
            score -= len(found_medical) * 15
            warnings.append(f"发现医疗相关词汇: {', '.join(found_medical[:3])}")
        
        # 检查虚假承诺
        false_words = self.sensitive_words.get('false_promises', [])
        found_false = [w for w in false_words if w in text]
        if found_false:
            score -= len(found_false) * 10
            warnings.append(f"发现绝对化用语: {', '.join(found_false[:3])}")
        
        # 检查平台违规
        platform_words = self.sensitive_words.get('platform_violations', [])
        found_platform = [w for w in platform_words if w in text]
        if found_platform:
            score -= len(found_platform) * 20
            warnings.append(f"发现平台违规词: {', '.join(found_platform[:3])}")
        
        return {
            "score": max(score, 0),
            "analysis": f"{'发现' if warnings else '未发现'}敏感词，合规性{'需优化' if warnings else '良好'}",
            "warnings": warnings if warnings else ["未发现敏感词，可放心发布"],
            "suggestions": ["建议替换敏感词，使用更温和的表达"] if warnings else []
        }
    
    def _analyze_seo(self, text: str, industry_id: str) -> Dict:
        """SEO分析"""
        score = 70
        suggestions = []
        
        # 加载行业关键词
        try:
            industry_file = os.path.join(self.industries_dir, f'{industry_id}.json')
            with open(industry_file, 'r', encoding='utf-8') as f:
                industry_data = json.load(f)
                industry_keywords = industry_data.get('keywords', [])
        except:
            industry_keywords = []
        
        # 检查关键词覆盖
        if industry_keywords:
            matched = [k for k in industry_keywords if k in text]
            coverage = len(matched) / min(len(industry_keywords), 10) * 100
            score = int(coverage)
            
            if coverage < 30:
                suggestions.append(f"关键词覆盖率{coverage:.0f}%，建议添加更多行业关键词")
            
            # 推荐未使用的关键词
            unused = [k for k in industry_keywords[:20] if k not in text]
            if unused:
                suggestions.append(f"推荐添加关键词: {', '.join(unused[:5])}")
        
        # 检查话题标签
        hashtag_pattern = r'#\w+'
        hashtags = re.findall(hashtag_pattern, text)
        if len(hashtags) >= 5:
            score += 10
        else:
            suggestions.append(f"当前话题标签{len(hashtags)}个，建议添加至5-8个")
        
        return {
            "score": min(score, 100),
            "analysis": f"关键词覆盖率{score}%，话题标签{len(hashtags)}个",
            "suggestions": suggestions if suggestions else ["SEO优化良好，搜索可见度高"]
        }
    
    def _generate_improved_version(self, title: str, body: str, dimensions: Dict) -> str:
        """生成优化建议版本"""
        suggestions = []
        
        for dim_name, dim_data in dimensions.items():
            if dim_data.get('suggestions'):
                suggestions.extend(dim_data['suggestions'][:2])
        
        if not suggestions:
            return "文案质量良好，暂无优化建议"
        
        return "优化建议：\n" + "\n".join(f"{i+1}. {s}" for i, s in enumerate(suggestions[:5]))


# 便捷函数
def diagnose_copy(title: str, body: str, industry_id: str) -> Dict:
    """
    便捷函数：诊断文案
    
    Args:
        title: 标题
        body: 正文
        industry_id: 行业ID
    
    Returns:
        诊断报告
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(base_dir)
    
    diagnosis = CopyDiagnosis(
        industries_dir=os.path.join(parent_dir, 'industries'),
        formulas_dir=os.path.join(parent_dir, 'formulas'),
        diagnosis_dir=base_dir
    )
    
    return diagnosis.diagnose(title, body, industry_id)


if __name__ == '__main__':
    # 测试
    print("🔍 文案诊断测试")
    print("-" * 50)
    
    test_title = "3支黄皮素颜口红！显白不挑皮"
    test_body = """姐妹们，今天分享3支我私藏的素颜神器

💄第一支：超显白
这支真的绝了！黄皮涂上去直接白一个度

💄第二支：超滋润
这支是我的心头好，日常通勤必备

💄第三支：超持久
这支是最近的宝藏发现，性价比超高

✨觉得有用的话记得点赞收藏哦！

#美妆分享 #口红试色 #黄皮显白"""
    
    result = diagnose_copy(test_title, test_body, "beauty")
    
    print(f"\n总评分: {result['overall_score']}/100\n")
    print("各维度评分:")
    for dim_name, dim_data in result['dimensions'].items():
        print(f"  {dim_name}: {dim_data['score']}/100")
    print(f"\n优化建议:\n{result['improved_version']}")
