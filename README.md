# 小红书爆款文案生成器

## 简介
一个小红书爆款文案工具箱（Claude Code Skill）：推荐由 Claude 主写作；脚本提供行业素材/热点匹配/结构化约束/文案诊断等能力。

## 功能特性
- ✍️ **一行出稿（默认）**：`行业|主题[|风格]` → 直接生成完整文案
- 🧩 **批量出稿**：`xN/×N` 或 `--variants N` 一次出多条，方便 A/B 测试
- 🎭 **风格人设**：支持「闺蜜分享 / 专业测评 / 学霸笔记 / 吐槽避雷 / 温柔治愈 / 自律教练」
- 🤖 **可选 AI 增强**：`--ai` 接入大模型做二次润色（默认仍是离线模板；无 key 自动回退）
- 🧰 **工具模式（推荐给 Claude Code）**：`--brief/--hot/--diagnose + --json` 输出结构化数据，适合多次调用
- 🎯 **高级 3 步流程**：选题 → 标题 → 正文（手动挑选）
- 📊 **5维文案诊断**：点击率、完读率、转化力、合规性、SEO
- 🔥 **热点智能推荐**：内置50+热点场景
- 💾 **历史记录管理**：可选保存、查看、删除
- 🏭 **10行业模板**：美妆、穿搭、美食、旅行等

## Claude Skill vs Python CLI

这套项目有两种常见使用方式：

| 场景 | 谁是主作者 | Python 脚本的角色 | 默认行为 |
|---|---|---|---|
| 在 Claude Code 里当 Skill 用（推荐） | Claude（LLM） | 提供数据与校验工具：brief/hot/diagnose（可多次调用） | Claude 主写文案；脚本不需要自己“写成品” |
| 直接运行 `python skill.py` | 脚本（离线模板）或外部 LLM | 生成草稿 +（可选）调用 API 做润色 | 不加 `--ai` 就是离线模板；加 `--ai` 才会调用大模型 |

所以：**Python 直接跑 = 离线模板**；想要“真 AI 润色”就用 `--ai`（可选）。

## 推荐用法：在 Claude Code 里用（Claude 主写）

你不需要手动运行任何 `python` 命令。安装好 skill 后，直接在 Claude Code 里告诉 Claude：

- 主题一行给清楚：`行业|主题|风格`（例如：`美妆|春季防晒|专业测评`）
- 再补一句：要几条、是否要热点借势、有没有禁用词/合规要求

Claude 会在后台按需调用脚本（例如 `--brief --json` / `--hot --json` / `--diagnose --json`）拿到行业素材与诊断结果，然后由 Claude 输出最终文案。

## 快速开始

### 安装
1. 克隆或下载本项目
2. 确保已安装 Python 3.8+
3. 无需额外依赖，使用标准库即可

### 安装到 Claude Skill

把整个目录放到你的 skills 目录里即可（要求根目录存在 `SKILL.md`）。

```bash
# 1) 克隆仓库
git clone https://github.com/fantasysea/xiaohongshu-copywriting.git

# 2) 复制到全局 skills 目录（推荐）
mkdir -p ~/.claude/skills
cp -r xiaohongshu-copywriting ~/.claude/skills/

# 3) 验证
ls ~/.claude/skills/xiaohongshu-copywriting/SKILL.md
```

如果你是把 skill 安装到某个项目下，也可以用项目级目录：

```bash
mkdir -p YourProject/.claude/skills
cp -r xiaohongshu-copywriting YourProject/.claude/skills/
ls YourProject/.claude/skills/xiaohongshu-copywriting/SKILL.md
```

### 使用
```bash
# 进入项目目录
cd xiaohongshu-copywriting

# 手动运行（可选）：快速模式（默认）一行输入直接出稿
python skill.py

# 例如：输入一行
# 美妆|黄皮显白口红
```

### 工具模式（结构化 JSON，推荐给 Claude Code）

```bash
# 生成写作 brief（行业素材 + 结构约束 + 热点角度）
python skill.py --brief "美妆|春季防晒|专业测评" --json

# 只查热点
python skill.py --hot "春季防晒" --industry 美妆 --limit 3 --json

# 诊断一条文案（标题+正文）
python skill.py --diagnose --industry 美妆 --title "..." --body "..." --json
```

### AI 增强模式（可选）

当你希望输出更像“真人写的”，可以用 `--ai` 让大模型对离线草稿做二次编辑。没有配置 key 时会自动回退到离线结果，不影响正常使用。

1) Anthropic Claude（推荐）

```bash
export ANTHROPIC_API_KEY="your_key"
python skill.py "美妆|春季防晒|专业测评" --ai

# 可选：指定模型（也可用环境变量 ANTHROPIC_MODEL）
python skill.py "美妆|春季防晒" --ai --model "claude-3-5-sonnet-latest"
```

2) OpenAI

```bash
export OPENAI_API_KEY="your_key"
python skill.py "美妆|春季防晒" --ai --provider openai

# 可选：指定模型（也可用环境变量 OPENAI_MODEL）
python skill.py "美妆|春季防晒" --ai --provider openai --model "gpt-4o-mini"
```

注意：项目不会保存你的 key；请使用环境变量，不要把 key 写进仓库。

### 快速模式（默认）
- 输入格式支持：
  - `行业|主题`（推荐）
  - `行业|主题|风格`（可选风格）
  - `主题`（自动识别行业；识别失败默认美妆）
- 只问一次，不再让你选选题/标题，也不再问是否保存
- 批量出稿（仍然只问一次）：
  - 在输入末尾加 `xN` / `×N`，例如：`美妆|春季防晒 x3`
  - 或用参数：`python skill.py "美妆|春季防晒" --variants 3`
- 热点辅助（自动、轻量）：当主题匹配到内置热点时，会提示一个「借势角度」并融入生成结果

#### 风格（可选）
你可以在输入里加第三段（或用 `--style`）：
- `闺蜜分享`（默认）
- `专业测评`
- `学霸笔记`
- `吐槽避雷`
- `温柔治愈`
- `自律教练`

示例：
```bash
python skill.py "美妆|春季防晒|专业测评" --variants 3
```

### 高级模式（保留 3 步问答）
如果你想手动挑选题、挑标题：

```bash
python skill.py --advanced
```

高级模式会走原来的 3 步流程：选题 → 标题 → 正文，并可选择是否保存。

## 命令/参数
- `python skill.py`：快速模式（默认）
- `python skill.py --advanced`：高级 3 步模式
- `python skill.py "[行业|]主题" --variants N`：快速模式直接出 N 条
- `python skill.py "[行业|]主题" --style "专业测评"`：指定风格
- `python skill.py "[行业|]主题" --save`：保存到本地历史（默认不保存）
- `python skill.py "[行业|]主题" --ai [--provider anthropic|openai] [--model ...]`：可选 AI 润色（需要环境变量 API key）
- `python skill.py --brief "行业|主题|风格" --json`：输出写作 brief（结构化 JSON）
- `python skill.py --hot "主题" [--industry 美妆] [--limit 5]`：热点推荐
- `python skill.py --hot "主题" --json`：热点推荐（结构化 JSON）
- `python skill.py --diagnose --title "标题" --body "正文" [--industry 美妆]`：文案诊断
- `python skill.py --diagnose --json`：文案诊断（结构化 JSON）
- `python skill.py --history [--limit 20] [--industry 美妆]`：查看历史
- `python skill.py --history --show <id>`：查看某条历史详情
- `python skill.py --history --delete <id>`：删除某条历史

### 常用示例

快速出 3 条（并借势热点）：
```bash
python skill.py "美妆|春季防晒" --variants 3
# 或：交互输入 美妆|春季防晒 x3
```

只看热点推荐（不生成正文）：
```bash
python skill.py --hot "春季防晒" --industry 美妆 --limit 5
```

诊断已有文案：
```bash
python skill.py --diagnose --industry 美妆 --title "3支黄皮素颜口红" --body "姐妹们..."
```

生成并保存，然后查看历史：
```bash
python skill.py "美妆|春季防晒" --save
python skill.py --history --limit 10
```

### 模块功能

#### 1. 文案生成 (`skill.py`)
```python
from skill import CopywritingGenerator

generator = CopywritingGenerator()
# 运行交互式生成流程
generator.run()
```

#### 2. 文案诊断 (`diagnosis/engine.py`)
```python
from diagnosis.engine import diagnose_copy

result = diagnose_copy(
    title="3支黄皮素颜口红！显白不挑皮",
    body="姐妹们，今天分享...",
    industry_id="beauty"
)
# 返回5维度评分和优化建议
```

#### 3. 热点推荐 (`hot_topics/matcher.py`)
```python
from hot_topics.matcher import match_hot_topics

results = match_hot_topics(
    user_input="春季防晒霜",
    industry="beauty",
    top_k=3
)
# 返回最相关的热点及借势角度
```

#### 4. 历史记录 (`data/storage.py`)
```python
from data.storage import save_copy, get_history

# 保存文案
copy_id = save_copy({
    "title": "...",
    "full_content": "...",
    "industry": "beauty"
})

# 获取历史记录
history = get_history(limit=10)
```

## 项目结构
```
xiaohongshu-copywriting/
├── skill.py                 # 主程序入口
├── llm/                      # 可选：LLM API 客户端（--ai）
├── config.json              # 全局配置
├── README.md                # 使用说明
├── industries/              # 行业模板（10个行业）
│   ├── beauty.json          # 美妆护肤
│   ├── fashion.json         # 时尚穿搭
│   ├── food.json            # 美食探店
│   ├── travel.json          # 旅行攻略
│   ├── education.json       # 知识付费
│   ├── career.json          # 职场成长
│   ├── parenting.json       # 母婴育儿
│   ├── home.json            # 家居生活
│   ├── fitness.json         # 健身减肥
│   └── tech.json            # 数码科技
├── formulas/                # 标题公式（12种）
│   ├── pain_solution.json   # 痛点解决方案型
│   ├── number_list.json     # 数字清单型
│   ├── contrast.json        # 对比冲突型
│   ├── question_hook.json   # 悬念提问型
│   ├── avoid_pitfall.json   # 避坑指南型
│   ├── quick_learn.json     # 速成教学型
│   ├── scarcity.json        # 稀缺限定型
│   ├── emotion.json         # 情感共鸣型
│   ├── review_compare.json  # 测评对比型
│   ├── challenge.json       # 挑战实验型
│   ├── free_gift.json       # 福利赠送型
│   └── hot_topic.json       # 热点借势型
├── hot_topics/              # 热点系统
│   ├── builtin.json         # 内置50+热点
│   ├── matcher.py          # 热点匹配算法
│   └── api_config.json      # API配置模板
├── diagnosis/               # 诊断模块
│   ├── engine.py           # 5维诊断引擎
│   └── sensitive_words.json # 敏感词库
└── data/                    # 数据存储
    ├── storage.py          # 存储管理器
    └── history.json        # 历史记录（自动生成）
```

## 配置说明

### 全局配置 (`config.json`)
```json
{
  "settings": {
    "default_industry": "beauty",    // 默认行业
    "emoji_style": "moderate",       // emoji风格
    "auto_save": true                // 自动保存
  },
  "limits": {
    "title_max_length": 20,          // 标题最大长度
    "ideas_count": 5,                // 生成选题数量
    "titles_count": 5                // 生成标题数量
  }
}
```

### 实时热点API配置 (`hot_topics/api_config.json`)
如需实时热点，可申请以下API：
- 知乎热榜（无需key）
- NewsAPI（免费版）
- 微博API（需开发者账号）

编辑 `api_config.json` 填入API key即可启用。

## 使用示例

### 示例1：生成美妆文案
```
$ python skill.py

🏭 请选择行业：
1. 💄 美妆护肤 - 彩妆、护肤、美容相关
2. 👗 时尚穿搭 - 服装搭配、OOTD...
...

请输入数字选择 (1-10): 1

💭 今天想写什么主题？（如：春季防晒、Excel技巧）: 黄皮显白口红

📌 Step 1: 选题灵感
...

📝 Step 2: 标题创作
...

✨ Step 3: 正文生成
...
```

### 示例2：诊断已有文案
```python
from diagnosis.engine import diagnose_copy

result = diagnose_copy(
    title="今天给大家分享一个很好用的面膜",
    body="这个面膜真的很好用...",
    industry_id="beauty"
)

print(f"总评分: {result['overall_score']}/100")
for dim_name, dim_data in result['dimensions'].items():
    print(f"{dim_name}: {dim_data['score']}/100")
```

## 扩展开发

### 添加新行业
1. 在 `industries/` 目录创建新的JSON文件
2. 参考 `template.json` 格式填写行业数据
3. 至少包含50个关键词、20个emoji、30个话题标签

### 添加新公式
1. 在 `formulas/` 目录创建新的JSON文件
2. 定义模板变量和示例
3. 关联适合的行业

### 添加新热点
1. 编辑 `hot_topics/builtin.json`
2. 在对应类别下添加热点数据
3. 设置有效期和适合行业

## 注意事项

1. **合规性**：生成的文案请遵守小红书社区规范
2. **敏感词**：系统会自动检测敏感词，但请人工复核
3. **原创性**：生成的文案仅供参考，建议根据实际情况调整
4. **API限制**：实时热点API有调用限制，请合理使用

## 更新日志

### v1.0.0 (2025-01)
- ✅ 3步交互生成流程
- ✅ 10行业模板
- ✅ 12种标题公式
- ✅ 5维文案诊断
- ✅ 热点智能推荐
- ✅ 历史记录管理

## 贡献指南

欢迎提交Issue和PR！

## 许可证

MIT License

---

**Made with ❤️ for 小红书创作者**
