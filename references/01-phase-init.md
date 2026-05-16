# Phase 1: 项目初始化

## 目标

建立项目骨架，定义目录结构和配置文件。这是整个Agent系统的地基，必须稳固。

## 前置条件

> **重要：在开始Phase 1之前，必须先完成需求确认。**
> 如果用户没有明确技术栈、LLM供应商、Agent规模等信息，请先询问用户（参考SKILL.md中的"需求确认"章节），确认后再开始构建。

### 需要确认的信息

| 问题 | 默认值 | 说明 |
|------|--------|------|
| **技术栈** | Python | 决定项目脚手架语言 |
| **LLM供应商** | Anthropic | 决定默认配置 |
| **Agent规模** | 中型 | 决定项目复杂度 |
| **主要用途** | 编码助手 | 决定工具集 |
| **多Agent协作** | 否 | 决定是否需要额外模块 |

### 目录结构变体

根据技术栈选择，目录结构中的入口文件有所不同：

```bash
# Python版本
my-agent/
├── pyproject.toml / requirements.txt
├── src/
│   ├── main.py              # 入口文件

# Node.js版本
my-agent/
├── package.json
├── src/
│   ├── main.js              # 入口文件
```

## 理论指导

### 应用的设计原则

1. **Context Engineering（上下文工程）**：目录结构即信息的可访问性
   - 核心代码放在 `src/` 目录下，用户配置放在 `config/` 目录下
   - 这种结构让Agent能清晰区分"框架代码"和"用户自定义"
   - 类比：就像操作系统区分系统文件和用户文件

2. **Architectural Constraints（架构约束）**：通过目录结构建立边界
   - `src/` 目录是只读的（框架升级时会覆盖）
   - `config/`、`skills/`、`workspace/` 是用户可修改的
   - 这种约束防止用户误改核心代码

### 为什么需要这种结构？

想象一个Agent项目运行了3个月：
- 用户添加了20个自定义skill
- 框架发布了新版本，修复了关键bug
- 如果skill和核心代码混在一起，升级时用户需要手动合并
- 如果目录结构清晰，升级只需要替换 `src/` 目录

## 实践步骤

### 步骤1：创建标准目录结构

```bash
my-agent/
├── README.md                    # 项目说明和启动指南（必须）
├── pyproject.toml / package.json  # 依赖管理
├── .env.example                   # 环境变量模板
├── .gitignore                     # Git忽略规则
├── config/                        # 用户配置目录（完全可修改）
│   ├── settings.yaml              # 主配置文件
│   └── agents/                    # Agent角色定义
├── src/                           # 核心框架代码（只读，升级时覆盖）
│   ├── main.py / index.ts         # 入口文件
│   ├── agent/                     # Agent核心模块
│   ├── tools/                     # 工具实现
│   ├── llm/                       # LLM客户端抽象
│   ├── permissions/               # 权限系统
│   └── utils/                     # 工具函数
├── skills/                        # 用户可扩展的skills目录
├── memory/                        # 记忆持久化存储（.gitignore）
├── workspace/                     # Agent工作区
└── tests/                         # 测试用例
```

### 步骤2：创建主配置文件

文件：`config/settings.yaml`

```yaml
# 类型: 用户配置
# 说明: Agent主配置文件，控制Agent的核心行为

# LLM配置
llm:
  provider: "anthropic"  # anthropic | openai | azure | local
  model: "claude-sonnet-4-20250514"
  api_key: "${ANTHROPIC_API_KEY}"  # 从环境变量读取
  base_url: null  # 自定义API端点（本地模型需要）
  max_tokens: 4096
  temperature: 0.7

# Agent配置
agent:
  name: "my-agent"
  description: "一个智能编码助手"
  max_turns: 50
  context_window: 200000

# 工具配置
tools:
  enabled:
    - "file_tools"
    - "network_tools"
    - "browser_tools"
  disabled: []

# 权限配置
permissions:
  mode: "ask"  # allow | deny | ask
  rules:
    - pattern: "Bash(rm -rf *)"
      action: "deny"
    - pattern: "Bash(sudo *)"
      action: "deny"

# 沙箱配置
sandbox:
  enabled: true
  allowed_directories:
    - "workspace/"
  denied_patterns:
    - ".env"
    - ".env.*"
    - "*.key"
    - "*.pem"
    - "secrets/"

# 记忆配置
memory:
  enabled: true
  storage: "memory/"
  max_size: "100MB"
  auto_compact: true

# 日志配置
logging:
  level: "info"  # debug | info | warning | error
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: "logs/agent.log"
```

### 步骤3：创建环境变量模板

文件：`.env.example`

```bash
# LLM配置
LLM_PROVIDER=anthropic
LLM_MODEL=claude-sonnet-4-20250514
LLM_MAX_TOKENS=4096
LLM_TEMPERATURE=0.7

# Anthropic配置
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# OpenAI配置
OPENAI_API_KEY=your_openai_api_key_here

# Azure配置
AZURE_OPENAI_KEY=your_azure_openai_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com

# 本地模型配置
LOCAL_MODEL_BASE_URL=http://localhost:11434
LOCAL_MODEL_NAME=llama3.1

# 日志配置
LOG_LEVEL=info

# Agent配置
AGENT_NAME=my-agent
AGENT_MAX_TURNS=50
```

### 步骤4：创建项目README

文件：`README.md`

```markdown
# {{project_name}}

{{project_description}}

## 功能特性

- **多供应商LLM支持**: 支持Anthropic、OpenAI、Azure、本地模型等
- **模块化工具系统**: 可扩展的工具注册和执行机制
- **权限控制**: 细粒度的权限模型和Hook系统
- **上下文管理**: 四级压缩管道，高效利用上下文窗口
- **记忆系统**: 短期和长期记忆持久化
- **会话管理**: 不可变的会话日志，支持回放和恢复

## 快速开始

### 安装依赖

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt
```

### 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填入你的API密钥
```

### 启动Agent

```bash
python src/main.py
```

## 目录结构

```
{{project_name}}/
├── README.md              # 项目说明和启动指南
├── requirements.txt       # Python依赖
├── .env.example           # 环境变量模板
├── config/               # 用户配置目录
│   ├── settings.yaml      # 主配置文件
│   └── agents/           # Agent角色定义
├── src/                  # 核心框架代码
│   ├── main.py           # 入口文件
│   ├── agent/            # Agent核心模块
│   ├── tools/            # 工具实现
│   ├── llm/              # LLM客户端抽象
│   ├── permissions/       # 权限系统
│   └── utils/            # 工具函数
├── skills/               # 用户自定义Skill
├── memory/               # 记忆持久化存储
├── workspace/             # Agent工作区
└── tests/                # 测试用例
```

## 添加自定义Skill

1. 在 `skills/` 目录下创建新的skill文件
2. 编辑skill文件，定义触发条件和行为
3. 在 `src/skills/` 中实现对应的处理逻辑
4. 重启Agent，测试新skill

## 配置说明

### LLM供应商配置

| 供应商 | 环境变量 | 说明 |
|--------|---------|------|
| Anthropic | `ANTHROPIC_API_KEY` | Claude系列模型 |
| OpenAI | `OPENAI_API_KEY` | GPT系列模型 |
| Azure | `AZURE_OPENAI_KEY` + `AZURE_OPENAI_ENDPOINT` | Azure OpenAI |
| Local | `LOCAL_MODEL_BASE_URL` | 本地模型（Ollama/vLLM） |

### 权限配置

编辑 `config/settings.yaml` 配置权限规则：

```yaml
permissions:
  mode: "ask"  # allow | deny | ask
  rules:
    - pattern: "Bash(rm -rf *)"
      action: "deny"
```

## 常见问题

### Q: 如何切换LLM供应商？

A: 修改 `.env` 文件中的 `LLM_PROVIDER` 变量，然后重启Agent。

### Q: 如何添加新的工具？

A: 在 `src/tools/` 目录下创建新的工具模块，然后注册到工具注册表。

### Q: 记忆数据存储在哪里？

A: 记忆数据存储在 `memory/` 目录下，该目录已添加到 `.gitignore`。
```

## 检查清单

- [ ] 目录结构符合规范
- [ ] 配置文件包含LLM、Agent、工具、权限、记忆配置
- [ ] README包含安装、配置、启动说明
- [ ] .env.example包含所有必要的环境变量
- [ ] .gitignore排除了敏感信息和运行时数据
- [ ] 依赖文件（requirements.txt/package.json）包含所有必要的依赖

## 常见问题

### 问题：目录结构不清晰，核心代码和用户配置混在一起

**症状**：
- 用户不知道哪些文件可以修改
- 升级框架时用户文件被覆盖
- 配置文件散落在各处

**原因**：
- 缺乏明确的目录类型定义
- 没有区分"框架代码"和"用户配置"

**解决**：
- 严格区分 `src/`（核心框架）和 `config/`（用户配置）
- 在文件头部添加类型注释
- 提供目录结构说明文档

### 问题：环境变量管理混乱

**症状**：
- 敏感信息（API密钥）硬编码在代码中
- 不同环境（开发/测试/生产）使用相同的配置
- 新用户不知道需要配置哪些环境变量

**解决**：
- 使用 `.env.example` 模板
- 使用 `python-dotenv` 加载环境变量
- 敏感信息绝不提交到版本控制

### 问题：配置文件格式不统一

**症状**：
- 有些配置用YAML，有些用JSON，有些用环境变量
- 配置项散落在多个文件中
- 用户找不到配置项

**解决**：
- 统一使用YAML格式
- 所有配置集中在 `config/settings.yaml`
- 环境变量只用于敏感信息

## 下一步

完成Phase 1后，进入 **Phase 2: LLM抽象层**（参考 `references/02-phase-llm.md`）
