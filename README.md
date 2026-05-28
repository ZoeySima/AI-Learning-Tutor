# AI Learning Tutor — 用 AI 重新定义学习

一个基于 Claude 的个性化学习助手，帮你快速建立对陌生领域的「概念性理解」。

## 核心方法论

本工具实现了一套经过验证的 AI 学习四步法：

1. **Map**：生成全局认知地图（章节大纲），先建立框架
2. **Learn**：逐章深挖，每章用「三视角 + 真实例子」讲解
3. **Quiz**：每章末出题验证，答对才进下一章
4. **Loop**：循环直到所有章节完成

## 为什么有效？

- **个性化定制**：根据你的背景调整讲解颗粒度
- **主动验证**：不是被动阅读，而是通过出题暴露理解盲区
- **结构化记忆**：先建地图再填细节，新知识有挂钩

## 快速开始

### 安装

```bash
# 克隆仓库
git clone https://github.com/yourusername/ai-learning-tutor.git
cd ai-learning-tutor

# 安装依赖
pip install -r requirements.txt

# 或者使用 pip 安装（开发模式）
pip install -e .
```

### 配置 API Key

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

### 开始学习

```bash
# 开始新学习
ai-tutor start "区块链技术基础"

# 恢复已有会话
ai-tutor resume 20260527-blockchain

# 列出所有会话
ai-tutor list

# 导出学习笔记
ai-tutor export 20260527-blockchain -o notes.md
```

## 使用示例

```bash
$ ai-tutor start "金融衍生品基础"

欢迎使用 AI Learning Tutor！

请简单介绍你的背景（职业、已有知识）：
> 我是程序员，完全零基础

正在生成学习地图...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📚 学习地图：金融衍生品基础
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

全局概览：
金融衍生品是基于基础资产（股票、债券、商品等）价值变化的金融工具...

章节大纲：
  1. 核心概念（期权、期货、互换）
  2. 市场结构（交易所、OTC、清算）
  3. 定价原理（Black-Scholes、无套利）
  4. 风险管理（对冲、Greeks）
  5. 实际应用（案例分析）

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

准备好了吗？按回车开始第 1 章...
```

## 适用场景

- 快速了解陌生行业（接新项目、转岗准备）
- 学习新技术栈（编程语言、框架、工具）
- 补充领域知识（金融、法律、医学概念）
- 考试备考（建立知识框架）

## 项目结构

```
ai-learning-tutor/
├── ai_tutor/
│   ├── __init__.py
│   ├── __main__.py        # CLI 入口
│   ├── cli.py             # 命令行交互
│   ├── core.py            # 四步法核心引擎
│   ├── llm.py             # LLM 调用封装
│   ├── state.py           # 状态管理
│   └── prompts.py         # 提示词模板
├── examples/              # 示例会话
├── tests/                 # 测试
├── README.md
├── README_EN.md
├── LICENSE
├── pyproject.toml
└── requirements.txt
```

## 开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest

# 代码格式化
black ai_tutor/
ruff check ai_tutor/
```

## 方法论来源

本工具的方法论来自一篇关于「用 AI 学习」的实践文章，核心思想是：

> AI 越强，对人的要求其实是变高了。降低的是执行层的要求，但概念层的要求被抬高了。你得知道一件事是什么、为什么存在、和其他事物的关系是什么。

详见 [docs/methodology.md](docs/methodology.md)

## License

MIT License - 详见 [LICENSE](LICENSE)

## 贡献

欢迎提交 Issue 和 Pull Request！

## 致谢

- 方法论灵感来自微信公众号文章《学习这件事，正在被 AI 重新定义》
- 基于 [Anthropic Claude](https://www.anthropic.com/) API
- CLI 界面使用 [Rich](https://github.com/Textualize/rich)
