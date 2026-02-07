---
name: xiaohongshu-copywriting
description: 小红书爆款文案工具箱（Claude Code）：Claude 负责主写作，脚本提供行业/热点/约束/诊断等数据与校验。
version: 1.1.0
---

# 小红书爆款文案生成器（Tool-first / Claude 主写）

这个 Skill 的推荐用法是：在 Claude Code 里由 Claude 主写文案；本仓库的脚本主要提供数据、约束与校验（而不是“脚本自己写完”）。

你可以把它当成：
- Claude = 创意与写作引擎
- `skill.py` = 行业素材库 + 热点匹配 + 诊断评估（工具箱）

## 推荐工作流（Claude Code 内部用）

1) 收集用户输入
- 最好是一行：`行业|主题|风格`（行业/风格可省略）
- 还要问清楚：要几条（variants）、有没有硬性限制（字数、是否带品牌、是否可带产品名等）

2) 生成写作 brief（结构化约束 + 行业素材）

```bash
python skill.py --brief "美妆|春季防晒|专业测评" --json
```

3) 需要借势热点时（可选）

```bash
python skill.py --hot "春季防晒" --industry 美妆 --limit 3 --json
```

4) Claude 作为主作者输出最终文案

先看 brief 里的约束与素材，再写成品。输出必须遵守下面的“输出协议”。

5) 诊断与回改（强烈建议）

```bash
python skill.py --diagnose --industry 美妆 --title "..." --body "..." --json
```

如果合规/SEO/转化有警告：按 suggestions 修改后再诊断 1 次（最多 2 轮）。

## 输出协议（硬性要求）

目标：输出可以直接复制到小红书发布的文案。

- 只输出文案本体；不要输出解释、步骤、分析、免责声明、客套话
- 不要出现：`作为AI`、`仅供参考`、`以下是`、`希望对你有帮助` 等提示语
- 多条 variants：每条文案之间用一行 `---` 分隔（除此之外不加编号/标题）

每条文案格式必须是：

1) 第一行：标题（<= 20 字；不加“标题：”前缀）
2) 空一行
3) 正文：开头 1 段 + 正文 3-6 段 + CTA 1 段
   - 每段之间空一行
   - emoji 适中，只放在段首
   - 每段 1-2 句，避免大段长句
4) 空一行
5) 最后一行：话题标签（3-10 个；空格分隔；每个以 `#` 开头）

示例骨架（仅示意结构，不要照抄内容）：

```
<标题>

<开头段>

<正文段1>

<正文段2>

<正文段3>

<CTA>

#话题1 #话题2 #话题3
```

合规硬约束：
- 避免绝对化/保证性词（如：100%、最、第一、立刻见效、治好）
- 避免医疗承诺/夸大功效（用“体感/经验/可能因人而异/我自己的方法”替代）
- 不引战、不攻击群体、不制造焦虑（尤其在母婴/身材/职场主题）

## 工具调用策略（让脚本当工具，不当作者）

默认顺序：brief -> (hot 可选) -> 写作 -> diagnose -> (必要时回改再 diagnose)

1) brief（必调）

```bash
python skill.py --brief "行业|主题|风格" --json
```

2) hot（可选）
- 用户明确要求借势热点，或 brief 里 `hot.suggested_angle` 命中时调用

```bash
python skill.py --hot "主题" --industry 美妆 --limit 3 --json
```

3) diagnose（建议对每条成品都做一次）
- 如果出现 `warnings/suggestions` 或总分偏低：按建议回改后再跑 1 次（最多 2 轮，避免无限循环）

```bash
python skill.py --diagnose --industry 美妆 --title "..." --body "..." --json
```

## 多变体（variants）生成策略

当用户要 N 条时：每条必须“角度不同”，而不是同义改写。

建议的角度组合（按主题选择 2-4 个即可）：
- 清单盘点（收藏向）
- 避坑指南（反常识/踩雷）
- 对比测评（选择困难）
- 速成教程（步骤/流程）
- 真实体验（时间线/前后对比，但不夸大）

每条都要保持同一风格人设（bestie/pro/notes/roast/warm/coach），但切入点可以变。

## 工具命令说明（供 Claude 调用）

- `--brief`：把“行业/主题/风格”汇总成一个 JSON brief（关键词/hashtags/emoji/标题公式/结构约束/热点角度）
- `--hot`：只返回热点匹配结果
- `--diagnose`：对标题+正文做 5 维诊断并给建议
- `--json`：输出纯 JSON（stdout），便于模型稳定解析

## 重要说明

- 在 Claude Code 场景下，不需要 `--ai`。
  - `--ai` 是“纯 Python 运行时想调用外部大模型”的开关；在 Claude Code 里再调用一次外部 LLM 通常是多余且更耗费。
- 如果用户坚持要用纯 Python CLI，也可以直接：

```bash
python skill.py "美妆|春季防晒|专业测评" --variants 3
```
