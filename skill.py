#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小红书爆款文案生成器
Xiaohongshu Viral Copywriting Generator

功能：
- 3步交互生成流程（选题→标题→正文）
- 5维文案诊断
- 热点智能推荐
- 历史记录管理

作者：AI Assistant
版本：1.0.0
"""

import json
import os
import sys
import random
import argparse
import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

# 配置路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, 'config.json')
INDUSTRIES_DIR = os.path.join(BASE_DIR, 'industries')
FORMULAS_DIR = os.path.join(BASE_DIR, 'formulas')
HOT_TOPICS_DIR = os.path.join(BASE_DIR, 'hot_topics')
DIAGNOSIS_DIR = os.path.join(BASE_DIR, 'diagnosis')
DATA_DIR = os.path.join(BASE_DIR, 'data')


class CopywritingGenerator:
    """小红书文案生成器主类"""
    
    def __init__(self):
        """初始化生成器"""
        self.config = self._load_config()
        self.industries = self._load_industries()
        self.formulas = self._load_formulas()
        self.ai_options: Dict[str, Any] = {
            "enabled": False,
            "provider": "anthropic",
            "model": None,
            "max_tokens": 900,
            "temperature": 0.6,
            "timeout_s": 30,
        }

    def configure_ai(
        self,
        *,
        enabled: bool,
        provider: str = "anthropic",
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        timeout_s: Optional[int] = None,
    ) -> None:
        self.ai_options["enabled"] = bool(enabled)
        if provider:
            self.ai_options["provider"] = str(provider).strip().lower()
        if model is not None:
            self.ai_options["model"] = (str(model).strip() or None)
        if max_tokens is not None:
            self.ai_options["max_tokens"] = int(max_tokens)
        if temperature is not None:
            self.ai_options["temperature"] = float(temperature)
        if timeout_s is not None:
            self.ai_options["timeout_s"] = int(timeout_s)

    def _ai_enabled(self) -> bool:
        return bool((self.ai_options or {}).get("enabled"))

    def _try_parse_ai_json(self, text: str) -> Optional[Dict[str, Any]]:
        s = (text or "").strip()
        if not s:
            return None

        if s.startswith("```"):
            s = s.strip("`")
            s = s.replace("json\n", "", 1).strip()

        try:
            v = json.loads(s)
            return v if isinstance(v, dict) else None
        except Exception:
            pass

        l = s.find("{")
        r = s.rfind("}")
        if l != -1 and r != -1 and r > l:
            try:
                v = json.loads(s[l : r + 1])
                return v if isinstance(v, dict) else None
            except Exception:
                return None

        return None

    def _maybe_ai_enhance_copy(
        self,
        copy_data: Dict[str, Any],
        *,
        topic: str,
        industry_id: str,
        style_id: str,
        hot: Optional[Dict[str, Any]] = None,
        idea: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if not self._ai_enabled():
            return copy_data

        try:
            from llm.client import LLMError, default_model, enhance_copy, get_api_key
        except Exception:
            print("⚠️  AI增强不可用（缺少 llm 模块）", file=sys.stderr)
            return copy_data

        provider = str((self.ai_options or {}).get("provider") or "anthropic").strip().lower()
        api_key = get_api_key(provider)
        if not api_key:
            env_name = "ANTHROPIC_API_KEY" if provider == "anthropic" else "OPENAI_API_KEY"
            print(f"⚠️  未检测到 {env_name}，已跳过 AI 增强（仍使用离线模板）", file=sys.stderr)
            return copy_data

        model = str((self.ai_options or {}).get("model") or "").strip() or default_model(provider)
        max_tokens = int((self.ai_options or {}).get("max_tokens") or 900)
        temperature = float((self.ai_options or {}).get("temperature") or 0.6)
        timeout_s = int((self.ai_options or {}).get("timeout_s") or 30)

        industry = self.industries.get(industry_id, {}) or {}
        style_label = self._style_label(style_id)
        hot_line = ""
        if hot and hot.get("suggested_angle"):
            hot_line = str(hot.get("suggested_angle", "")).strip()

        draft_title = str(copy_data.get("title", "")).strip()
        draft_full = str(copy_data.get("full_content", "")).strip()
        draft_tags = copy_data.get("hashtags", []) or []
        draft_tags_str = " ".join([str(x).strip() for x in draft_tags if str(x).strip()])

        idea_title = ""
        idea_angle = ""
        if isinstance(idea, dict):
            idea_title = str(idea.get("title", "")).strip()
            idea_angle = str(idea.get("angle", "")).strip()

        prompt = (
            "你是中文小红书（XHS）爆款文案编辑。\n"
            "任务：在不改变主题与人设风格的前提下，提升点击/完读/收藏/转化。\n\n"
            "【硬性要求】\n"
            "- 只输出一个 JSON 对象（不要任何解释、不要 markdown）。\n"
            "- JSON 键：title, full_content, hashtags。\n"
            "- title：<=20字，避免空泛词与占位符。\n"
            "- full_content：只写正文（不含标题行），结构为：开头1段 + 正文3-6段 + CTA1段 + 最后一行话题标签。\n"
            "- emoji：适中，只放在段首；不要每句都加。\n"
            "- 合规：避免绝对化/虚假功效/医疗承诺/引战。\n"
            "- hashtags：数组，3-10个，元素形如 '#xxx'；full_content 最后一行把这些 hashtags 用空格拼起来。\n\n"
            f"【元信息】\n行业: {industry.get('name', industry_id)} ({industry_id})\n主题: {topic}\n风格人设: {style_label}\n"
            + (f"借势角度: {hot_line}\n" if hot_line else "")
            + (f"选题角度: {idea_angle}\n" if idea_angle else "")
            + (f"选题标题: {idea_title}\n" if idea_title else "")
            + "\n"
            "【草稿（请优化）】\n"
            + (f"草稿标题: {draft_title}\n" if draft_title else "")
            + (f"草稿标签: {draft_tags_str}\n" if draft_tags_str else "")
            + "草稿正文:\n"
            + draft_full
        )

        try:
            out = enhance_copy(
                provider=provider,
                api_key=api_key,
                model=model,
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                timeout_s=timeout_s,
            )
        except LLMError as e:
            print(f"⚠️  AI 增强失败，已回退到离线模板：{e}", file=sys.stderr)
            return copy_data
        except Exception as e:
            print(f"⚠️  AI 增强异常，已回退到离线模板：{e}", file=sys.stderr)
            return copy_data

        parsed = self._try_parse_ai_json(out)
        if not parsed:
            merged = dict(copy_data)
            if out.strip():
                merged["full_content"] = out.strip()
                merged["body"] = out.strip()
            merged["ai_provider"] = provider
            merged["ai_model"] = model
            return merged

        new_title = str(parsed.get("title", "") or "").strip()
        new_full = str(parsed.get("full_content", "") or "").strip()
        new_tags_raw = parsed.get("hashtags", [])
        new_tags: List[str] = []
        if isinstance(new_tags_raw, list):
            for t in new_tags_raw:
                ts = str(t).strip()
                if not ts:
                    continue
                if not ts.startswith("#"):
                    ts = "#" + ts.lstrip("#")
                new_tags.append(ts)
        new_tags = [x for x in new_tags if x]
        if len(new_tags) > 10:
            new_tags = new_tags[:10]

        merged = dict(copy_data)
        if new_title:
            merged["title"] = new_title
        if new_tags:
            merged["hashtags"] = new_tags
        if new_full:
            merged["full_content"] = new_full
            merged["body"] = new_full
        merged["ai_provider"] = provider
        merged["ai_model"] = model
        return merged
    
    def _load_config(self) -> Dict:
        """加载配置文件"""
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  加载配置失败: {e}")
            return {}
    
    def _load_industries(self) -> Dict[str, Dict]:
        """加载所有行业配置"""
        industries = {}
        try:
            for filename in os.listdir(INDUSTRIES_DIR):
                if filename.endswith('.json') and filename != 'template.json':
                    filepath = os.path.join(INDUSTRIES_DIR, filename)
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        industries[data['id']] = data
        except Exception as e:
            print(f"⚠️  加载行业配置失败: {e}")
        return industries
    
    def _load_formulas(self) -> Dict[str, Dict]:
        """加载所有标题公式"""
        formulas = {}
        try:
            for filename in os.listdir(FORMULAS_DIR):
                if filename.endswith('.json') and filename != 'template.json':
                    filepath = os.path.join(FORMULAS_DIR, filename)
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        formulas[data['id']] = data
        except Exception as e:
            print(f"⚠️  加载公式失败: {e}")
        return formulas

    def _default_industry_id(self) -> str:
        default_id = (self.config.get("settings", {}) or {}).get("default_industry")
        return default_id if default_id in self.industries else "beauty"

    def _resolve_industry_id_from_hint(self, hint: str) -> Optional[str]:
        raw = (hint or "").strip()
        if not raw:
            return None

        raw_lower = raw.lower()
        if raw_lower in self.industries:
            return raw_lower

        for ind_id, ind in self.industries.items():
            name = str(ind.get("name", ""))
            if raw in name or name in raw:
                return ind_id

        aliases = {
            "美妆": "beauty",
            "护肤": "beauty",
            "穿搭": "fashion",
            "时尚": "fashion",
            "ootd": "fashion",
            "美食": "food",
            "探店": "food",
            "旅行": "travel",
            "旅游": "travel",
            "攻略": "travel",
            "知识": "education",
            "学习": "education",
            "教育": "education",
            "职场": "career",
            "工作": "career",
            "面试": "career",
            "母婴": "parenting",
            "育儿": "parenting",
            "宝宝": "parenting",
            "家居": "home",
            "收纳": "home",
            "装修": "home",
            "健身": "fitness",
            "减肥": "fitness",
            "减脂": "fitness",
            "数码": "tech",
            "科技": "tech",
            "手机": "tech",
            "电脑": "tech",
        }
        for k, v in aliases.items():
            if k in raw_lower or k in raw:
                return v if v in self.industries else None

        return None

    def _auto_detect_industry_id(self, topic: str) -> str:
        t = (topic or "").strip()
        if not t:
            return self._default_industry_id()

        t_lower = t.lower()

        best_id = self._default_industry_id()
        best_hits = 0

        for ind_id, ind in self.industries.items():
            hits = 0
            for kw in ind.get("keywords", []) or []:
                k = str(kw).strip().lower()
                if not k:
                    continue
                if k in t_lower:
                    hits += 1

            if hits > best_hits:
                best_hits = hits
                best_id = ind_id

        return best_id

    def _parse_quick_text(self, text: str) -> Tuple[str, str, Optional[str]]:
        raw = (text or "").strip()
        if not raw:
            return self._default_industry_id(), "好物推荐", None

        sep = "|" if "|" in raw else ("｜" if "｜" in raw else "")
        if sep:
            parts = [p.strip() for p in raw.split(sep) if p.strip()]
            left = parts[0] if len(parts) >= 2 else ""
            topic = parts[1] if len(parts) >= 2 else (parts[0] if parts else "")
            style_hint = parts[2] if len(parts) >= 3 else None

            topic = (topic or "").strip() or "好物推荐"
            ind_id = self._resolve_industry_id_from_hint(left)
            if not ind_id:
                ind_id = self._auto_detect_industry_id(topic)
            return ind_id, topic, style_hint

        topic = raw
        return self._auto_detect_industry_id(topic), topic, None

    def _default_style_id(self, industry_id: str) -> str:
        mapping = {
            "beauty": "bestie",
            "fashion": "bestie",
            "food": "bestie",
            "travel": "notes",
            "education": "notes",
            "career": "pro",
            "parenting": "warm",
            "home": "warm",
            "fitness": "coach",
            "tech": "pro",
        }
        return mapping.get(industry_id, "bestie")

    def _resolve_style_id_from_hint(self, hint: Optional[str]) -> Optional[str]:
        raw = (hint or "").strip()
        if not raw:
            return None

        raw_lower = raw.lower()
        fixed = {
            "bestie": "bestie",
            "girlfriend": "bestie",
            "pro": "pro",
            "review": "pro",
            "notes": "notes",
            "study": "notes",
            "roast": "roast",
            "warm": "warm",
            "coach": "coach",
            "闺蜜": "bestie",
            "闺蜜风": "bestie",
            "专业": "pro",
            "专业测评": "pro",
            "测评": "pro",
            "学霸": "notes",
            "笔记": "notes",
            "学霸笔记": "notes",
            "吐槽": "roast",
            "吐槽避雷": "roast",
            "避雷": "roast",
            "温柔": "warm",
            "治愈": "warm",
            "教练": "coach",
            "打卡": "coach",
        }
        if raw_lower in fixed:
            return fixed[raw_lower]
        if raw in fixed:
            return fixed[raw]

        if any(k in raw for k in ["专业", "测评", "理性", "参数", "对比"]):
            return "pro"
        if any(k in raw for k in ["学霸", "笔记", "干货", "公式", "步骤"]):
            return "notes"
        if any(k in raw for k in ["吐槽", "避雷", "别买", "千万别", "坑"]):
            return "roast"
        if any(k in raw for k in ["温柔", "治愈", "松弛", "生活感"]):
            return "warm"
        if any(k in raw for k in ["教练", "打卡", "训练", "自律", "坚持"]):
            return "coach"
        if any(k in raw for k in ["闺蜜", "姐妹", "安利", "种草"]):
            return "bestie"

        return None

    def _style_label(self, style_id: str) -> str:
        labels = {
            "bestie": "闺蜜分享",
            "pro": "专业测评",
            "notes": "学霸笔记",
            "roast": "吐槽避雷",
            "warm": "温柔治愈",
            "coach": "自律教练",
        }
        return labels.get(style_id, style_id)

    def _extract_variants_hint(self, text: str) -> Tuple[str, int]:
        raw = (text or "").strip()
        if not raw:
            return raw, 1

        m = re.search(r"\s*[x×]\s*(\d+)\s*$", raw, flags=re.IGNORECASE)
        if not m:
            return raw, 1

        try:
            n = int(m.group(1))
        except ValueError:
            return raw, 1

        n = max(1, min(n, 10))
        return raw[: m.start()].strip(), n

    def _suggest_hot_angle(self, topic: str, industry_id: str) -> Optional[Dict[str, Any]]:
        try:
            from hot_topics.matcher import match_hot_topics
        except Exception:
            return None

        try:
            results = match_hot_topics(topic, industry_id, top_k=1)
        except Exception:
            return None

        if not results:
            return None

        top = results[0]
        if float(top.get("relevance_score", 0)) < 60:
            return None

        return top

    def get_hot_suggestions(self, text: str, industry: Optional[str] = None, top_k: int = 5) -> Dict[str, Any]:
        raw = (text or "").strip()
        if not raw:
            return {"ok": False, "error": "empty_topic", "results": []}

        ind_id = self._resolve_industry_id_from_hint(industry or "")
        if not ind_id:
            ind_id = self._auto_detect_industry_id(raw)

        try:
            from hot_topics.matcher import match_hot_topics
        except Exception:
            return {"ok": False, "error": "hot_topics_unavailable", "industry_id": ind_id, "topic": raw, "results": []}

        try:
            results = match_hot_topics(raw, ind_id, top_k=top_k)
        except Exception:
            return {"ok": False, "error": "hot_topics_failed", "industry_id": ind_id, "topic": raw, "results": []}

        ind = self.industries.get(ind_id, {}) or {}
        return {
            "ok": True,
            "industry_id": ind_id,
            "industry": {"id": ind_id, "name": ind.get("name", ""), "icon": ind.get("icon", ""), "description": ind.get("description", "")},
            "topic": raw,
            "results": results or [],
        }

    def diagnose_copy(self, title: str, body: str, industry: Optional[str] = None) -> Dict[str, Any]:
        t = (title or "").strip()
        b = body or ""
        if not t:
            return {"ok": False, "error": "empty_title"}

        ind_id = self._resolve_industry_id_from_hint(industry or "")
        if not ind_id:
            ind_id = self._auto_detect_industry_id(t + " " + b)

        try:
            from diagnosis.engine import diagnose_copy
        except Exception:
            return {"ok": False, "error": "diagnosis_unavailable", "industry_id": ind_id}

        try:
            result = diagnose_copy(t, b, ind_id)
        except Exception:
            return {"ok": False, "error": "diagnosis_failed", "industry_id": ind_id}

        return {"ok": True, "industry_id": ind_id, "title": t, "result": result}

    def build_brief(self, text: str, industry: Optional[str] = None, style: Optional[str] = None) -> Dict[str, Any]:
        raw = (text or "").strip()
        if not raw:
            return {"ok": False, "error": "empty_input"}

        industry_id, topic, style_hint = self._parse_quick_text(raw)

        # allow overrides via flags
        ind_override = self._resolve_industry_id_from_hint(industry or "")
        if ind_override:
            industry_id = ind_override
        elif not industry_id:
            industry_id = self._auto_detect_industry_id(topic)

        style_id = (
            self._resolve_style_id_from_hint(style)
            or self._resolve_style_id_from_hint(style_hint)
            or self._default_style_id(industry_id)
        )

        ind = self.industries.get(industry_id, {}) or {}
        keywords = [str(x).strip() for x in (ind.get("keywords", []) or []) if str(x).strip()]
        hashtags = [str(x).strip() for x in (ind.get("hashtags", []) or []) if str(x).strip()]
        emojis = [str(x).strip() for x in (ind.get("emojis", []) or []) if str(x).strip()]

        # formulas recommended by industry
        formula_ids = ind.get("formulas", []) or []
        formula_items: List[Dict[str, Any]] = []
        for fid in formula_ids:
            f = self.formulas.get(str(fid), {}) or {}
            if not f:
                continue
            formula_items.append({
                "id": f.get("id", str(fid)),
                "name": f.get("name", ""),
                "template": f.get("template", ""),
            })
            if len(formula_items) >= 6:
                break

        style_notes = {
            "bestie": ["口吻像闺蜜分享", "更偏种草/体验", "emoji适中，段首点缀"],
            "pro": ["结论先行，讲维度/标准", "少空话，多可执行", "emoji偏少"],
            "notes": ["像笔记，条理清晰", "多清单/步骤/公式", "适合收藏"],
            "roast": ["吐槽但给解决方案", "突出避雷点", "语气犀利但不攻击"],
            "warm": ["温柔、松弛感", "减压/陪伴式表达", "避免制造焦虑"],
            "coach": ["打卡/训练计划感", "强调执行与复盘", "适合挑战/阶段目标"],
        }

        hot = self._suggest_hot_angle(topic, industry_id)
        title_max = int((self.config.get("limits", {}) or {}).get("title_max_length", 20))

        return {
            "ok": True,
            "topic": topic,
            "industry": {
                "id": industry_id,
                "name": ind.get("name", ""),
                "icon": ind.get("icon", ""),
                "description": ind.get("description", ""),
            },
            "style": {"id": style_id, "label": self._style_label(style_id), "notes": style_notes.get(style_id, [])},
            "hot": hot,
            "keywords": keywords[:20],
            "hashtags": hashtags[:12],
            "emojis": emojis[:12],
            "formulas": formula_items,
            "constraints": {
                "title_max_length": title_max,
                "full_content_structure": ["开头1段", "正文3-6段", "CTA1段", "最后一行话题标签"],
                "compliance": ["避免绝对化/医疗承诺/虚假功效", "避免引战与敏感词", "用体验与方法替代承诺"],
            },
        }

    def _render_title_template(self, template: str, idea: Dict, industry: Dict, topic: str) -> str:
        t = template or ""
        ind_name = str(industry.get("name", ""))

        people_map = {
            "beauty": "黄皮",
            "fashion": "小个子",
            "food": "吃货",
            "travel": "第一次去的你",
            "education": "零基础",
            "career": "打工人",
            "parenting": "新手爸妈",
            "home": "租房党",
            "fitness": "小基数",
            "tech": "新手",
        }
        default_people = "新手"

        replacements = {
            "稀缺身份": random.choice(["内部员工", "柜姐", "教练", "HR", "本地人", "过来人"]),
            "秘密": random.choice(["技巧", "清单", "秘诀", "方法", "避坑"]),
            "数字": str(random.randint(3, 10)),
            "内容类型": str(idea.get("title", topic))[:6] or topic[:6],
            "内容": str(idea.get("title", topic))[:6] or topic[:6],
            "价值点": "超实用",
            "价值": "超实用",
            "痛点": "困扰很久",
            "解决方案": "这套方法",
            "效果": "真的有用",
            "Before": "月薪3k",
            "After": "月薪3w",
            "转折内容": "我的实操方法",
            "疑问词": "为什么",
            "人群": people_map.get(str(industry.get("id", "")), default_people),
            "秘密行为": f"都在用{topic}",
            "警示词": "千万别",
            "产品": topic,
            "时间": random.choice(["3分钟", "5分钟", "10分钟", "7天"]),
            "技能": topic,
            "年龄": random.choice(["25岁", "30岁", "35岁"]),
            "真相": random.choice(["干货", "套路", "真相", "方法"]),
            "测评类型": random.choice(["横向测评", "真实测评", "深度测评"]),
            "年份": str(datetime.now().year),
            "时间跨度": random.choice(["7天", "30天", "一周"]),
            "转折": random.choice(["第3天就破功了", "结果出乎意料", "我真的震惊了"]),
            "福利提示": random.choice(["免费领取", "限时分享", "福利整理"]),
            "方向": random.choice(["穿搭", "妆容", "效率", "拍照"]),
            "趋势": random.choice(["真的回潮了", "太适合通勤了", "普通人也能学"]),
            "热点IP": "热播剧",
        }

        for k, v in replacements.items():
            t = t.replace("{" + k + "}", str(v))

        t = re.sub(r"\{[^}]+\}", "", t)
        t = t.replace("  ", " ").strip()
        t = re.sub(r"\|{2,}", "|", t)
        t = t.replace("|", "｜")
        t = re.sub(r"｜{2,}", "｜", t)
        t = t.strip("｜ ")

        if not t:
            t = f"{topic}｜{ind_name}干货"

        return t

    def run_quick_mode(self, text: Optional[str] = None, variants: int = 1, style: Optional[str] = None, save: bool = False) -> List[Dict]:
        raw = text
        if raw is None:
            raw = input("输入（可选：行业|主题[|风格] 或 主题；可加 xN 生成多条）：").strip()

        raw, hint_variants = self._extract_variants_hint(raw)
        variants = max(1, min(max(int(variants or 1), hint_variants), 10))

        industry_id, topic, style_hint = self._parse_quick_text(raw)
        industry = self.industries.get(industry_id, {})

        style_id = self._resolve_style_id_from_hint(style) or self._resolve_style_id_from_hint(style_hint) or self._default_style_id(industry_id)

        hot = self._suggest_hot_angle(topic, industry_id)

        print("\n" + "=" * 50)
        print("📝 小红书爆款文案生成器（快速模式）")
        if industry:
            print(f"🏭 行业: {industry.get('icon', '')} {industry.get('name', industry_id)}")
        print(f"💭 主题: {topic}")
        print(f"🎭 风格: {self._style_label(style_id)}")
        print("=" * 50)

        outputs: List[Dict] = []
        for i in range(variants):
            ideas = self.generate_ideas(topic, industry_id)
            selected_idea = ideas[i % len(ideas)] if ideas else {"title": topic, "angle": "清单盘点"}

            if hot and hot.get("suggested_angle"):
                selected_idea = dict(selected_idea)
                angle_prefix = str(hot.get("suggested_angle", "")).split("｜", 1)[0].strip()
                if angle_prefix and angle_prefix not in str(selected_idea.get("title", "")):
                    selected_idea["title"] = f"{angle_prefix}｜{selected_idea.get('title', topic)}"

            titles_count = int((self.config.get("limits", {}) or {}).get("titles_count", 5))
            titles = self.generate_titles(selected_idea, industry_id, count=titles_count)
            if titles:
                titles_sorted = sorted(titles, key=lambda x: x.get("score", 0), reverse=True)
                pick_pool = titles_sorted[: min(3, len(titles_sorted))]
                selected_title = pick_pool[i % len(pick_pool)]
            else:
                selected_title = {"text": topic}

            content = self.generate_content(selected_title.get("text", topic), selected_idea, industry_id, style_id=style_id)
            content = self._maybe_ai_enhance_copy(
                content,
                topic=topic,
                industry_id=industry_id,
                style_id=style_id,
                hot=hot,
                idea=selected_idea,
            )
            content["industry"] = industry_id
            content["formula_used"] = selected_title.get("formula")
            content["score"] = selected_title.get("score")
            outputs.append(content)

            if variants > 1:
                print(f"\n--- 文案 {i+1}/{variants} ---")

            if hot and hot.get("topic") and hot.get("suggested_angle"):
                topic_name = str(hot["topic"].get("name", "")).strip()
                angle = str(hot.get("suggested_angle", "")).strip()
                if angle and topic_name and angle.startswith(topic_name):
                    print(f"🔥 借势热点: {angle}")
                else:
                    print(f"🔥 借势热点: {topic_name}｜{angle}".strip("｜"))

            print("\n" + "=" * 50)
            print(content.get("full_content", ""))
            print("=" * 50)

            if save:
                try:
                    from data.storage import LocalStorage
                    storage = LocalStorage(DATA_DIR)
                    copy_id = storage.save_copy(content)
                    print(f"💾 已保存: {copy_id}")
                except Exception:
                    print("⚠️  保存失败")

        print("\n提示：运行 `python skill.py --advanced` 进入3步模式")

        return outputs

    def run_hot_mode(self, text: Optional[str] = None, industry: Optional[str] = None, top_k: int = 5) -> List[Dict]:
        raw = (text or "").strip()
        if not raw:
            raw = input("输入主题（用于匹配热点）：").strip()
        if not raw:
            print("❌ 主题为空")
            return []

        payload = self.get_hot_suggestions(raw, industry=industry, top_k=top_k)
        if not payload.get("ok"):
            print("❌ 热点模块不可用")
            return []

        ind = payload.get("industry", {}) or {}
        ind_id = payload.get("industry_id")
        results = payload.get("results", []) or []
        print("\n" + "=" * 50)
        print("🔥 热点推荐")
        print(f"🏭 行业: {ind.get('icon', '')} {ind.get('name', ind_id)}")
        print(f"💭 主题: {raw}")
        print("=" * 50)

        if not results:
            print("未匹配到热点（可以换个更具体的关键词试试）")
            return []

        for i, r in enumerate(results, 1):
            t = r.get("topic", {})
            score = r.get("relevance_score", 0)
            mk = r.get("matched_keywords", [])
            angle = r.get("suggested_angle", "")
            print(f"{i}. {t.get('name', '')}  (相关度: {score:.1f}/100  热度: {t.get('heat', '')})")
            if mk:
                print(f"   匹配词: {', '.join(mk)}")
            if angle:
                print(f"   借势角度: {angle}")
            print()

        return results

    def run_diagnose_mode(self, title: Optional[str] = None, body: Optional[str] = None, industry: Optional[str] = None) -> Dict:
        t = (title or "").strip()
        b = body

        if not t:
            t = input("请输入标题：").strip()

        if b is None:
            b = input("请输入正文（可直接粘贴一段）：").strip()

        payload = self.diagnose_copy(t, b or "", industry=industry)
        if not payload.get("ok"):
            print("❌ 诊断模块不可用")
            return {}

        ind_id = str(payload.get("industry_id") or "").strip()
        result = payload.get("result", {}) or {}
        ind = self.industries.get(ind_id, {}) if ind_id else {}
        print("\n" + "=" * 50)
        print("🔍 文案诊断")
        print(f"🏭 行业: {ind.get('icon', '')} {ind.get('name', ind_id)}")
        print(f"🧾 标题: {t}")
        print("=" * 50)
        print(f"总评分: {result.get('overall_score', 0)}/100\n")

        dims = result.get("dimensions", {}) or {}
        for name in ["click_rate", "completion_rate", "conversion", "compliance", "seo"]:
            d = dims.get(name, {}) or {}
            if not d:
                continue
            print(f"- {name}: {d.get('score', 0)}/100")
            analysis = d.get("analysis")
            if analysis:
                print(f"  {analysis}")
            warnings = d.get("warnings") or []
            if warnings:
                print(f"  warnings: {', '.join(warnings[:3])}")
            suggestions = d.get("suggestions") or []
            if suggestions:
                print(f"  suggestions: {', '.join(suggestions[:3])}")

        improved = result.get("improved_version")
        if improved:
            print("\n" + improved)

        return result

    def run_history_mode(self, limit: int = 20, industry: Optional[str] = None, show: Optional[str] = None, delete: Optional[str] = None) -> None:
        try:
            from data.storage import LocalStorage
            storage = LocalStorage(DATA_DIR)
        except Exception:
            print("❌ 历史模块不可用")
            return

        if delete:
            ok = storage.delete_copy(delete)
            print("✅ 已删除" if ok else "❌ 未找到该ID")
            return

        if show:
            rec = storage.get_copy_by_id(show)
            if not rec:
                print("❌ 未找到该ID")
                return
            print("\n" + "=" * 50)
            print(f"🧾 {rec.get('id', '')}")
            print(f"🏭 {rec.get('industry', '')}  {rec.get('created_at', '')}")
            print(f"标题: {rec.get('title', '')}")
            print("=" * 50)
            print(rec.get("body", ""))
            return

        ind_id = self._resolve_industry_id_from_hint(industry or "")
        history = storage.get_history(limit=limit, industry=ind_id)
        if not history:
            print("（暂无历史记录）")
            return

        print("\n" + "=" * 50)
        print("📚 历史记录")
        if ind_id:
            ind = self.industries.get(ind_id, {})
            print(f"筛选行业: {ind.get('icon', '')} {ind.get('name', ind_id)}")
        print("=" * 50)

        for i, rec in enumerate(history, 1):
            rid = rec.get("id", "")
            title = rec.get("title", "")
            created = rec.get("created_at", "")
            indv = rec.get("industry", "")
            print(f"{i}. {rid}  [{indv}]  {created}")
            if title:
                print(f"   {title}")

        print("\n提示：使用 `python skill.py --history --show <id>` 查看详情")
    
    def select_industry(self) -> str:
        """选择行业"""
        print("\n🏭 请选择行业：")
        industries_list = list(self.industries.items())
        for i, (ind_id, ind_data) in enumerate(industries_list, 1):
            print(f"{i}. {ind_data['icon']} {ind_data['name']} - {ind_data['description']}")
        
        while True:
            try:
                choice = input("\n请输入数字选择 (1-{}): ".format(len(industries_list)))
                idx = int(choice) - 1
                if 0 <= idx < len(industries_list):
                    selected_id = industries_list[idx][0]
                    print(f"✅ 已选择: {self.industries[selected_id]['icon']} {self.industries[selected_id]['name']}")
                    return selected_id
                else:
                    print("❌ 无效选择，请重新输入")
            except ValueError:
                print("❌ 请输入数字")
    
    def generate_ideas(self, topic: str, industry_id: str) -> List[Dict]:
        """
        Step 1: 基于主题和行业生成选题灵感
        
        Args:
            topic: 用户输入的主题
            industry_id: 行业ID
        
        Returns:
            5个选题灵感
        """
        industry = self.industries.get(industry_id, {})
        keywords = industry.get('keywords', [])
        sample_topics = industry.get('sample_topics', [])
        
        # 基于主题和关键词生成选题
        ideas = []
        
        # 选题1: 清单型
        ideas.append({
            "id": 1,
            "title": f"{topic}必看清单｜{random.choice(keywords[:10]) if keywords else '精选'}推荐",
            "angle": "清单盘点",
            "target_audience": "新手入门",
            "hook": "全面整理，一次搞定"
        })
        
        # 选题2: 避坑型
        ideas.append({
            "id": 2,
            "title": f"{topic}避坑指南｜这5个错误千万别犯",
            "angle": "避坑指南",
            "target_audience": "避免踩坑",
            "hook": "血泪教训，帮你省钱"
        })
        
        # 选题3: 对比型
        ideas.append({
            "id": 3,
            "title": f"{topic}对比测评｜{random.choice(keywords[:10]) if keywords else '热门'}产品怎么选",
            "angle": "对比测评",
            "target_audience": "选择困难症",
            "hook": "真实测评，不吹不黑"
        })
        
        # 选题4: 教程型
        ideas.append({
            "id": 4,
            "title": f"3分钟学会{topic}｜{random.choice(keywords[:10]) if keywords else '新手'}也能快速上手",
            "angle": "速成教程",
            "target_audience": "零基础",
            "hook": "简单易学，快速见效"
        })
        
        # 选题5: 经验型
        ideas.append({
            "id": 5,
            "title": f"{topic}真实体验｜用了一个月后的感受",
            "angle": "真实体验",
            "target_audience": "想了解真实效果",
            "hook": "亲测分享，真实可靠"
        })
        
        return ideas
    
    def generate_titles(self, idea: Dict, industry_id: str, count: int = 5) -> List[Dict]:
        """
        Step 2: 基于选题生成标题
        
        Args:
            idea: 选中的选题
            industry_id: 行业ID
            count: 生成标题数量
        
        Returns:
            标题列表
        """
        industry = self.industries.get(industry_id, {})
        emojis = industry.get('emojis', ['✨'])
        formula_ids = industry.get('formulas', ['number_list'])
        
        titles: List[Dict] = []
        pool = list(dict.fromkeys(formula_ids))
        if not pool:
            pool = ["number_list"]

        random.shuffle(pool)
        topic_hint = str(idea.get("title", ""))

        attempt = 0
        while len(titles) < count and attempt < len(pool) * 2:
            formula_id = pool[attempt % len(pool)]
            attempt += 1

            formula = self.formulas.get(formula_id, {})
            template = str(formula.get("template", "{内容}｜{价值}"))
            rendered = self._render_title_template(template, idea, {**industry, "id": industry_id}, topic_hint)
            if "{" in rendered or "}" in rendered:
                continue

            if random.random() > 0.3 and emojis:
                rendered = random.choice(emojis[:5]) + rendered

            rendered = rendered.strip()
            if len(rendered) > 20:
                rendered = rendered[:20]
                rendered = rendered.rstrip("｜ ")

            if not rendered:
                continue

            titles.append({
                "id": len(titles) + 1,
                "text": rendered,
                "formula": formula_id,
                "formula_name": formula.get("name", ""),
                "score": random.randint(70, 95),
                "why": f"使用{formula.get('name', '')}，符合{industry.get('name', '')}行业特点"
            })

        return titles
    
    def generate_content(self, title: str, idea: Dict, industry_id: str, style_id: Optional[str] = None) -> Dict:
        """
        Step 3: 基于标题生成完整文案
        
        Args:
            title: 选中的标题
            idea: 选题信息
            industry_id: 行业ID
        
        Returns:
            完整文案
        """
        industry = self.industries.get(industry_id, {})
        emojis = industry.get('emojis', ['✨'])
        hashtags = industry.get('hashtags', ['#分享'])
        keywords = industry.get('keywords', [])

        style_id = style_id or self._default_style_id(industry_id)

        if style_id in {"pro", "notes"}:
            emoji_pool = emojis[:2] if emojis else ["✨"]
        elif style_id == "coach":
            emoji_pool = emojis[:4] if emojis else ["✨"]
        else:
            emoji_pool = emojis
        
        angle = str(idea.get("angle", ""))

        if style_id == "pro":
            openings = [
                f"{random.choice(emoji_pool)}结论先行：关于「{idea.get('title', title)}」怎么选/怎么做更省心。",
                f"{random.choice(emoji_pool)}先说结论：这篇把「{idea.get('title', title)}」按维度讲透。",
                f"{random.choice(emoji_pool)}理性测评：围绕「{idea.get('title', title)}」给你可执行的建议。",
            ]
        elif style_id == "notes":
            openings = [
                f"{random.choice(emoji_pool)}一页笔记：{idea.get('title', title)}（建议收藏）。",
                f"{random.choice(emoji_pool)}干货笔记：{idea.get('title', title)}，照着做就行。",
                f"{random.choice(emoji_pool)}学习笔记整理：{idea.get('title', title)}（少走弯路版）。",
            ]
        elif style_id == "roast":
            openings = [
                f"{random.choice(emoji_pool)}拜托，{idea.get('title', title)}别再这样做了…真的容易踩雷。",
                f"{random.choice(emoji_pool)}我忍不住了：{idea.get('title', title)}这几个坑太多人中招。",
                f"{random.choice(emoji_pool)}吐槽归吐槽，但{idea.get('title', title)}按这套做更稳。",
            ]
        elif style_id == "warm":
            openings = [
                f"{random.choice(emoji_pool)}温柔提醒：{idea.get('title', title)}其实可以更轻松一点。",
                f"{random.choice(emoji_pool)}慢慢来：关于{idea.get('title', title)}，把关键点做好就够了。",
                f"{random.choice(emoji_pool)}今天分享一个更不焦虑的版本：{idea.get('title', title)}。",
            ]
        elif style_id == "coach":
            openings = [
                f"{random.choice(emoji_pool)}打卡式攻略：{idea.get('title', title)}，按这几步执行。",
                f"{random.choice(emoji_pool)}自律但不苦：{idea.get('title', title)}用更稳的方式做。",
                f"{random.choice(emoji_pool)}训练思路：关于{idea.get('title', title)}，先把基础做对。",
            ]
        else:
            openings = [
                f"{random.choice(emoji_pool)}姐妹们，今天把「{idea.get('title', title)}」说清楚！",
                f"{random.choice(emoji_pool)}被问爆的「{idea.get('title', title)}」我整理成一篇了！",
                f"{random.choice(emoji_pool)}亲测总结：关于「{idea.get('title', title)}」别再乱试了！",
            ]
        opening = random.choice(openings)

        body_paragraphs: List[str] = []
        k1 = random.choice(keywords[:30]) if keywords else "重点"
        k2 = random.choice(keywords[:30]) if keywords else "细节"
        k3 = random.choice(keywords[:30]) if keywords else "方法"

        if angle == "清单盘点":
            body_paragraphs = [
                f"{random.choice(emoji_pool)}1）先看{k1}：适合什么人、什么场景，一句话就能判断要不要买/做。",
                f"{random.choice(emoji_pool)}2）再看{k2}：避开最容易踩雷的点（比如过度/不适合/不匹配）。",
                f"{random.choice(emoji_pool)}3）最后看{k3}：用最省事的方式落地（我更推荐先从基础款开始）。",
            ]
        elif angle == "避坑指南":
            body_paragraphs = [
                f"{random.choice(emoji_pool)}坑1：只看热门不看{k1} → 很容易不适合自己。",
                f"{random.choice(emoji_pool)}坑2：忽略{k2}这个条件 → 结果不是没效果就是体验差。",
                f"{random.choice(emoji_pool)}坑3：步骤顺序错了（先做A再做B）→ 直接白忙。",
                f"{random.choice(emoji_pool)}✅正确做法：先确定需求（你最在意什么）→ 再选方案 → 最后复盘调整。",
            ]
        elif angle == "对比测评":
            body_paragraphs = [
                f"{random.choice(emoji_pool)}对比维度：{k1} / {k2} / {k3}（这3个最影响体验）。",
                f"{random.choice(emoji_pool)}适合A的人：追求稳定省心；适合B的人：追求强效果但愿意多折腾。",
                f"{random.choice(emoji_pool)}我的建议：先选更匹配你的场景（通勤/日常/特殊场合），别被营销带跑。",
            ]
        elif angle == "速成教程":
            body_paragraphs = [
                f"{random.choice(emoji_pool)}Step 1：先搞清楚你的目标（想要更{k1}还是更{k2}）。",
                f"{random.choice(emoji_pool)}Step 2：只做关键动作：先做1个最有效的步骤，再加1个加分步骤。",
                f"{random.choice(emoji_pool)}Step 3：做完立刻验证：看结果/看体感，不对就把变量收窄（别一次改太多）。",
            ]
        else:
            body_paragraphs = [
                f"{random.choice(emoji_pool)}使用前：我最困扰的是「{title}」相关的问题（反复踩雷）。",
                f"{random.choice(emoji_pool)}第3天：开始有变化，尤其在{k1}这块更明显。",
                f"{random.choice(emoji_pool)}第7天：稳定下来，{k2}的体验更好，整体更省事。",
                f"{random.choice(emoji_pool)}一个月后：我更在意{k3}的长期效果，所以会继续按这个思路迭代。",
            ]
        
        # 生成CTA
        if style_id == "pro":
            ctas = [
                f"{random.choice(emoji_pool)}如果你告诉我你的需求/预算/肤质(或场景)，我可以给更精准的建议。",
                f"{random.choice(emoji_pool)}收藏这篇，下次选的时候直接对照维度看。",
                f"{random.choice(emoji_pool)}想看同类对比我再补一篇（评论区告诉我）。",
            ]
        elif style_id == "notes":
            ctas = [
                f"{random.choice(emoji_pool)}建议收藏：下次直接按这张清单执行。",
                f"{random.choice(emoji_pool)}想要模板/清单版，我可以再整理一份。",
                f"{random.choice(emoji_pool)}如果你需要更细的步骤，我可以按你的场景补充。",
            ]
        elif style_id == "roast":
            ctas = [
                f"{random.choice(emoji_pool)}别再踩坑了…收藏一下，真的能省很多钱和时间。",
                f"{random.choice(emoji_pool)}你踩过哪个坑？评论区让我避雷也避你雷。",
                f"{random.choice(emoji_pool)}想看更狠的避雷清单？我继续更。",
            ]
        elif style_id == "warm":
            ctas = [
                f"{random.choice(emoji_pool)}慢慢来就好，收藏一下，哪天需要再翻出来看。",
                f"{random.choice(emoji_pool)}如果你愿意说说你的情况，我可以帮你更温柔地调整方案。",
                f"{random.choice(emoji_pool)}希望这篇能让你轻松一点。",
            ]
        elif style_id == "coach":
            ctas = [
                f"{random.choice(emoji_pool)}建议先坚持7天，别追求一次到位。",
                f"{random.choice(emoji_pool)}收藏打卡：照着做，稳定比爆发更重要。",
                f"{random.choice(emoji_pool)}想要更细的计划，我可以按你的时间表拆解。",
            ]
        else:
            ctas = [
                f"{random.choice(emoji_pool)}觉得有用的话记得点赞收藏哦！",
                f"{random.choice(emoji_pool)}有问题评论区问我，看到都会回复！",
                f"{random.choice(emoji_pool)}关注我，分享更多{industry.get('name', '')}干货！",
            ]
        cta = random.choice(ctas)
        
        # 组合话题标签
        selected_hashtags = random.sample(hashtags, min(8, len(hashtags)))
        hashtag_text = ' '.join(selected_hashtags)
        
        # 组合完整文案
        body = '\n\n'.join(body_paragraphs)
        full_content = f"{opening}\n\n{body}\n\n{cta}\n\n{hashtag_text}"
        
        return {
            "title": title,
            "opening": opening,
            "body": body,
            "cta": cta,
            "hashtags": selected_hashtags,
            "full_content": full_content,
            "formatting": "建议每段之间空一行，emoji放在段落开头"
        }
    
    def run_generate_mode(self):
        """运行生成模式（3步流程）"""
        print("\n" + "="*50)
        print("🎯 小红书爆款文案生成器")
        print("="*50)
        
        # Step 0: 选择行业
        industry_id = self.select_industry()
        
        # 输入主题
        topic = input(f"\n💭 今天想写什么主题？（如：春季防晒、Excel技巧）: ").strip()
        if not topic:
            topic = "好物推荐"
        
        # Step 1: 生成选题
        print("\n" + "-"*50)
        print("📌 Step 1: 选题灵感")
        print("-"*50)
        
        ideas = self.generate_ideas(topic, industry_id)
        print(f"\n基于「{topic}」，为你生成{len(ideas)}个选题灵感：\n")
        
        for idea in ideas:
            print(f"{idea['id']}. {idea['title']}")
            print(f"   切入角度: {idea['angle']} | 目标人群: {idea['target_audience']}")
            print(f"   核心卖点: {idea['hook']}\n")
        
        # 选择选题
        while True:
            try:
                choice = input("请选择选题 (1-{}): ".format(len(ideas)))
                idea_idx = int(choice) - 1
                if 0 <= idea_idx < len(ideas):
                    selected_idea = ideas[idea_idx]
                    break
                else:
                    print("❌ 无效选择")
            except ValueError:
                print("❌ 请输入数字")
        
        # Step 2: 生成标题
        print("\n" + "-"*50)
        print("📝 Step 2: 标题创作")
        print("-"*50)
        
        titles = self.generate_titles(selected_idea, industry_id)
        print(f"\n为你生成{len(titles)}个标题选项：\n")
        
        for title in titles:
            print(f"{title['id']}. {title['text']}")
            print(f"   公式: {title['formula_name']} | 预估点击率: {title['score']}/100")
            print(f"   💡 {title['why']}\n")
        
        # 选择标题
        while True:
            try:
                choice = input("请选择标题 (1-{}): ".format(len(titles)))
                title_idx = int(choice) - 1
                if 0 <= title_idx < len(titles):
                    selected_title = titles[title_idx]
                    break
                else:
                    print("❌ 无效选择")
            except ValueError:
                print("❌ 请输入数字")
        
        # Step 3: 生成正文
        print("\n" + "-"*50)
        print("✨ Step 3: 正文生成")
        print("-"*50)
        
        style_id = self._default_style_id(industry_id)
        content = self.generate_content(selected_title['text'], selected_idea, industry_id, style_id=style_id)
        content = self._maybe_ai_enhance_copy(
            content,
            topic=topic,
            industry_id=industry_id,
            style_id=style_id,
            idea=selected_idea,
        )
        
        print("\n🎉 生成的完整文案：\n")
        print("="*50)
        print(content['full_content'])
        print("="*50)
        
        # 保存选项
        save = input("\n💾 是否保存到历史记录？(y/n): ").strip().lower()
        if save == 'y':
            self._save_to_history(content, industry_id)
            print("✅ 已保存到历史记录")
        
        return content
    
    def _save_to_history(self, content: Dict, industry_id: str):
        """保存到历史记录"""
        try:
            os.makedirs(DATA_DIR, exist_ok=True)
            history_file = os.path.join(DATA_DIR, 'history.json')
            
            # 读取现有历史
            history = []
            if os.path.exists(history_file):
                with open(history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            
            # 添加新记录
            record = {
                "id": f"copy_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "title": content['title'],
                "body": content['full_content'],
                "industry": industry_id,
                "hashtags": content['hashtags'],
                "created_at": datetime.now().isoformat()
            }
            history.append(record)
            
            # 保存
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"⚠️  保存失败: {e}")
    
    def run(self):
        """主运行循环"""
        while True:
            try:
                content = self.run_generate_mode()
                
                again = input("\n🔄 是否继续生成？(y/n): ").strip().lower()
                if again != 'y':
                    print("\n👋 感谢使用小红书爆款文案生成器！")
                    break
                    
            except KeyboardInterrupt:
                print("\n\n👋 已退出")
                break
            except Exception as e:
                print(f"\n❌ 发生错误: {e}")
                continue


def main():
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("text", nargs="?", help="One-line input: [industry|]topic")

    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--advanced", action="store_true", help="Use interactive 3-step flow")
    mode.add_argument("--brief", action="store_true", help="Output writing brief/context (tool mode)")
    mode.add_argument("--hot", action="store_true", help="Show hot topic suggestions")
    mode.add_argument("--diagnose", action="store_true", help="Diagnose an existing copy")
    mode.add_argument("--history", action="store_true", help="Show saved history")

    parser.add_argument("--variants", type=int, default=1, help="Generate N variants in quick mode (default 1)")
    parser.add_argument("--style", type=str, default=None, help="Style/persona (e.g. 专业测评/学霸笔记/吐槽避雷)")
    parser.add_argument("--save", action="store_true", help="Save outputs to history (quick mode)")

    parser.add_argument("--ai", action="store_true", help="Enhance output using an LLM API (requires env API key)")
    parser.add_argument("--provider", type=str, default="anthropic", choices=["anthropic", "openai"], help="LLM provider for --ai")
    parser.add_argument("--model", type=str, default=None, help="Override LLM model for --ai")

    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON to stdout (tooling)")

    parser.add_argument("--industry", type=str, default=None, help="Industry id or Chinese hint")
    parser.add_argument("--limit", type=int, default=5, help="Limit for --hot/--history")
    parser.add_argument("--show", type=str, default=None, help="Show a history record by id")
    parser.add_argument("--delete", type=str, default=None, help="Delete a history record by id")
    parser.add_argument("--title", type=str, default=None, help="Title for --diagnose")
    parser.add_argument("--body", type=str, default=None, help="Body for --diagnose")
    args = parser.parse_args()

    generator = CopywritingGenerator()
    generator.configure_ai(enabled=bool(args.ai), provider=args.provider, model=args.model)
    if args.advanced:
        print("📝 小红书爆款文案生成器（高级模式）")
        print("版本 1.0.0")
        print("=" * 50)
        generator.run()
        return

    if args.brief:
        payload = generator.build_brief(args.text or "", industry=args.industry, style=args.style)
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            if not payload.get("ok"):
                print("❌ 生成 brief 失败")
                return
            ind = payload.get("industry", {}) or {}
            st = payload.get("style", {}) or {}
            print("\n" + "=" * 50)
            print("🧭 写作 Brief")
            print(f"🏭 行业: {ind.get('icon', '')} {ind.get('name', ind.get('id', ''))}")
            print(f"💭 主题: {payload.get('topic', '')}")
            print(f"🎭 风格: {st.get('label', st.get('id', ''))}")
            hot = payload.get("hot")
            if isinstance(hot, dict) and hot.get("suggested_angle"):
                print(f"🔥 借势角度: {hot.get('suggested_angle')}")
            print("=" * 50)
        return

    if args.hot:
        if args.json:
            payload = generator.get_hot_suggestions(args.text or "", industry=args.industry, top_k=args.limit)
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            generator.run_hot_mode(args.text, industry=args.industry, top_k=args.limit)
        return

    if args.diagnose:
        if args.json:
            payload = generator.diagnose_copy(args.title or "", args.body or "", industry=args.industry)
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            generator.run_diagnose_mode(title=args.title, body=args.body, industry=args.industry)
        return

    if args.history:
        if args.json:
            try:
                from data.storage import LocalStorage
                storage = LocalStorage(DATA_DIR)
                if args.delete:
                    ok = storage.delete_copy(args.delete)
                    payload = {"ok": bool(ok), "action": "delete", "id": args.delete}
                elif args.show:
                    rec = storage.get_copy_by_id(args.show)
                    payload = {"ok": bool(rec), "action": "show", "id": args.show, "record": rec}
                else:
                    ind_id = generator._resolve_industry_id_from_hint(args.industry or "")
                    history = storage.get_history(limit=args.limit, industry=ind_id)
                    payload = {"ok": True, "action": "list", "industry": ind_id, "limit": args.limit, "records": history}
                print(json.dumps(payload, ensure_ascii=False, indent=2))
            except Exception:
                print(json.dumps({"ok": False, "error": "history_unavailable"}, ensure_ascii=False, indent=2))
        else:
            generator.run_history_mode(limit=args.limit, industry=args.industry, show=args.show, delete=args.delete)
        return

    generator.run_quick_mode(args.text, variants=args.variants, style=args.style, save=args.save)


if __name__ == '__main__':
    main()
