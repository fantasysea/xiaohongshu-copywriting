# 小红书爆款文案生成器

## 基本信息

- **名称**: xiaohongshu-copywriting
- **版本**: 1.0.0
- **作者**: AI Assistant
- **描述**: 一个功能强大的小红书爆款文案生成器，支持3步交互生成流程、5维文案诊断、热点智能推荐

## 功能特性

- ✍️ **一行出稿（默认）**：`行业|主题[|风格]` → 直接生成完整文案
- 🧩 **批量出稿**：`xN/×N` 或 `--variants N` 一次出多条
- 🎭 **风格人设**：闺蜜分享 / 专业测评 / 学霸笔记 / 吐槽避雷 / 温柔治愈 / 自律教练
- 🎯 **高级 3 步流程**：选题 → 标题 → 正文
- 📊 **5维文案诊断**：点击率、完读率、转化力、合规性、SEO
- 🔥 **热点智能推荐**：内置50+热点场景
- 💾 **历史记录管理**：可选保存、查看、删除
- 🏭 **10行业模板**：美妆、穿搭、美食、旅行等

## 使用方法

### 方式1：命令行运行
```bash
# 快速模式（默认）：一行输入直接出稿
python skill.py

# 例如：三段输入（行业|主题|风格）
python skill.py "美妆|春季防晒|专业测评" --variants 3

# 高级模式：保留原3步问答
python skill.py --advanced

# 只看热点推荐
python skill.py --hot "春季防晒" --industry 美妆 --limit 5

# 诊断已有文案
python skill.py --diagnose --industry 美妆 --title "3支黄皮素颜口红" --body "姐妹们..."

# 查看历史（配合 --save）
python skill.py "美妆|春季防晒" --save
python skill.py --history --limit 10
```

### 方式2：作为模块导入
```python
from skill import CopywritingGenerator

generator = CopywritingGenerator()

# 快速模式（单次生成）
generator.run_quick_mode("美妆|黄皮显白口红")

# 高级模式（3步交互）
generator.run()
```

### 方式3：使用特定功能
```python
# 文案诊断
from diagnosis.engine import diagnose_copy
result = diagnose_copy(title, body, industry_id)

# 热点匹配
from hot_topics.matcher import match_hot_topics
results = match_hot_topics(user_input, industry, top_k=3)

# 历史记录
from data.storage import save_copy, get_history
save_copy(copy_data)
history = get_history(limit=10)
```

## 快速模式（默认）

- 输入格式支持：
  - `行业|主题`（推荐）
  - `行业|主题|风格`（可选）
  - `主题`（自动识别行业；识别失败默认美妆）
- 只问一次：不再让你选选题/标题，也不再问是否保存
- 批量出稿（仍然只问一次）：
  - 输入末尾加 `xN` / `×N`，例如：`美妆|春季防晒 x3`
  - 或命令行参数：`python skill.py "美妆|春季防晒" --variants 3`
- 热点辅助：当主题命中内置热点时，会提示一个借势角度并融入生成

风格可选值（中文/英文都可）：
- 闺蜜分享 (bestie)
- 专业测评 (pro)
- 学霸笔记 (notes)
- 吐槽避雷 (roast)
- 温柔治愈 (warm)
- 自律教练 (coach)

## 高级模式（3步生成流程）

运行 `python skill.py --advanced` 后：
1. 选择行业
2. 输入主题
3. 选选题 → 选标题 → 生成正文

## 支持行业

1. 💄 美妆护肤
2. 👗 时尚穿搭
3. 🍜 美食探店
4. ✈️ 旅行攻略
5. 📚 知识付费
6. 💼 职场成长
7. 👶 母婴育儿
8. 🏠 家居生活
9. 💪 健身减肥
10. 📱 数码科技

## 标题公式

内置12种爆款标题公式：
- 痛点解决方案型
- 数字清单型
- 对比冲突型
- 悬念提问型
- 避坑指南型
- 速成教学型
- 稀缺限定型
- 情感共鸣型
- 测评对比型
- 挑战实验型
- 福利赠送型
- 热点借势型

## 文件结构

```
xiaohongshu-copywriting/
├── SKILL.md               # 本文件 - skill说明
├── skill.py               # 主程序入口
├── config.json            # 全局配置
├── README.md              # 详细使用文档
├── industries/            # 10行业配置
├── formulas/              # 12种标题公式
├── hot_topics/            # 热点系统
├── diagnosis/             # 诊断模块
└── data/                  # 数据存储
```

## 配置说明

编辑 `config.json` 可自定义：
- 默认行业
- emoji风格
- 标题长度限制
- 历史记录数量

## 扩展API（可选）

如需实时热点，编辑 `hot_topics/api_config.json` 添加API key：
- 知乎热榜（无需key）
- NewsAPI（免费版）
- 微博API（需申请）

## 注意事项

1. 生成的文案请遵守小红书社区规范
2. 系统会自动检测敏感词，但请人工复核
3. 生成的文案仅供参考，建议根据实际情况调整

## 更新日志

### v1.0.0 (2025-01)
- ✅ 3步交互生成流程
- ✅ 10行业模板
- ✅ 12种标题公式
- ✅ 5维文案诊断
- ✅ 热点智能推荐
- ✅ 历史记录管理

## 许可证

MIT License
