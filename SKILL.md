---
name: agent-harness-engineer-v2
description: >
  指导AI coding工具构建生产级Agent系统。当用户需要设计、实现或优化AI Agent系统时触发。
  特别适用于：Agent架构设计、Harness工程、工具系统、权限模型、上下文管理、多智能体协作、
  记忆系统、安全沙箱、MCP集成等场景。支持从概念设计到生产部署的完整Agent系统构建。
  
  触发关键词：构建agent、创建智能体、agent系统、自动化工具、AI助手、多智能体、
  agent优化、升级agent、agent脚手架、agent项目模板、agent框架。
  
  核心目标：帮助AI coding工具生成结构完整、可扩展、生产就绪的Agent项目，
  而非仅提供最小化demo代码。
  
  与v1版本的区别：
  - v1版本：提供理论文档和最小示例，AI coding工具需要自己理解如何应用
  - v2版本：提供分阶段构建指南，每个阶段都有明确的理论指导、实践步骤、检查清单和常见问题
  - v2版本：AI coding工具按阶段执行，每个阶段都有明确的输入、输出和验收标准
---

# Agent Harness Engineer v2

本 Skill 将帮助你设计、实现和优化生产级的 AI Agent 系统，当前是v2版本。

本版本采用**分阶段构建模式**，将 Agent 系统构建拆分为 7 个明确的阶段，每个阶段都有：
- **理论指导**：该阶段需要应用什么设计原则
- **实践步骤**：具体要创建/修改哪些文件
- **检查清单**：完成标准是什么
- **常见问题**：这个阶段容易踩什么坑

## 快速导航

本 Skill 采用**分阶段构建模式**，核心内容分布在多个文件中：

- **[SKILL.md](SKILL.md)** (本文件): 核心原则、分阶段构建指南总览
- **[references/01-phase-init.md](references/01-phase-init.md)**: **Phase 1: 项目初始化** - 目录结构、配置文件、README
- **[references/02-phase-llm.md](references/02-phase-llm.md)**: **Phase 2: LLM抽象层** - 多供应商客户端、工厂函数
- **[references/03-phase-tools.md](references/03-phase-tools.md)**: **Phase 3: 工具系统** - 工具注册表、核心工具实现
- **[references/04-phase-agent-loop.md](references/04-phase-agent-loop.md)**: **Phase 4: Agent核心循环** - 状态机、错误恢复、终止原因
- **[references/05-phase-context.md](references/05-phase-context.md)**: **Phase 5: 上下文管理** - 四级压缩管道、记忆系统
- **[references/06-phase-permissions.md](references/06-phase-permissions.md)**: **Phase 6: 权限安全** - 权限模型、Hook系统、沙箱
- **[references/07-phase-production.md](references/07-phase-production.md)**: **Phase 7: 生产化** - 测试、监控、日志
- **[references/08-core-concepts.md](references/08-core-concepts.md)**: 核心概念速查（Harness Engineering三大支柱、三组件虚拟化架构）
- **[references/09-multi-agent.md](references/09-multi-agent.md)**: 多智能体协作、Coordinator模式、Swarm系统
- **[references/10-mcp-integration.md](references/10-mcp-integration.md)**: MCP协议、六种传输协议、配置示例
- **[templates/project-scaffold/](../templates/project-scaffold/)**: 完整项目脚手架模板（Python/Node.js）
- **[templates/README.md](../templates/README.md)**: 项目README模板

## 核心原则

### 1. Harness Engineering 三大支柱

- **Context Engineering（上下文工程）**: 管理信息的可访问性、结构和时机
  - 静态上下文：CLAUDE.md/AGENTS.md、设计文档
  - 动态上下文：日志、指标、Git状态、CI/CD状态
  - 上下文压缩：四级管道（Snip → Microcompact → Context-Collapse → Autocompact）
  - 核心原则: "Agent无法在上下文中访问的信息不存在"

- **Architectural Constraints（架构约束）**: 通过机械执行而非建议来建立边界
  - 权限模型：5种模式 × 7级规则层级
  - 工具约束：Schema验证、并发安全标记
  - 安全边界：沙盒隔离、硬编码拒绝、纵深防御

- **Entropy Management（熵管理）**: 定期清理Agent解决代码退化
  - 文档一致性验证、约束违规扫描、模式强制执行
  - 依赖审计、性能监控、覆盖率守卫

### 2. 三组件虚拟化架构

```
Session（会话）= 追加式事件日志（Append-only Event Log）
  - 不可变、可序列化、可回放
  - 类似数据库WAL，是系统的唯一事实来源
  - 支持故障恢复、负载迁移、调试回放

Harness（编排器）= 无状态编排循环
  - 全部输入来自Session日志
  - 可随时崩溃、重启、迁移
  - 给定同样的Session日志，任何实例都会做出同样决策

Sandbox（沙箱）= 隔离执行环境
  - 文件系统隔离、网络隔离、进程隔离
  - 凭证外置，按需创建和销毁
  - 限制爆炸半径（Blast Radius Containment）
```

## 需求确认（构建前的必要步骤）

> **重要：在开始构建Agent之前，必须先确认用户需求。**
> **如果用户已经明确提供了以下信息，可以跳过本环节。**
> **如果用户没有提供，AI coding工具必须主动询问用户做选择，不得自行决定。**

### 需要确认的问题

当用户说"帮我构建一个Agent"但没有明确说明以下信息时，AI coding工具必须主动询问：

| 问题 | 选项/说明 | 影响 |
|------|---------|------|
| **技术栈偏好？** | Python / Node.js / TypeScript / Go | 决定项目脚手架语言 |
| **LLM供应商？** | Anthropic / OpenAI / Azure / 本地模型 | 决定默认配置 |
| **Agent规模？** | 小型（个人助手）/ 中型（团队工具）/ 大型（企业平台） | 决定项目复杂度 |
| **主要用途？** | 编码助手 / 自动化运维 / 数据分析 / 通用对话 / 其他 | 决定工具集 |
| **部署环境？** | 本地 / 云服务器 / 容器 / Serverless | 决定配置方式 |
| **是否需要多Agent协作？** | 是 / 否 | 决定是否需要Phase 9内容 |

### 询问示例

如果用户说"帮我构建一个Agent"，但没有提供上述信息，AI coding工具应该这样询问：

```
在开始构建Agent之前，我需要确认几个问题：

1. **技术栈偏好**：你希望使用什么语言/框架？
   - Python（推荐，功能完善）
   - Node.js/TypeScript（如果你熟悉JS生态）

2. **LLM供应商**：你打算使用哪个LLM提供商？
   - Anthropic (Claude) - 复杂推理、长上下文
   - OpenAI (GPT) - 通用任务、生态丰富
   - Azure OpenAI - 企业合规、私有部署
   - 本地模型 (Ollama/vLLM) - 隐私敏感、离线环境

3. **Agent规模**：你的Agent主要用于什么场景？
   - 小型：个人助手，简单任务
   - 中型：团队协作，多功能
   - 大型：企业平台，高并发

4. **主要用途**：你的Agent主要做什么？
   - 编码助手
   - 自动化运维
   - 数据分析
   - 通用对话
   - 其他（请说明）

5. **是否需要多Agent协作**？
   - 是（需要并行处理复杂任务）
   - 否（单Agent足够）

请告诉我你的选择，我会根据你的需求构建最合适的Agent项目。
```

### 快速确认模式

如果用户已经提供了部分信息，AI coding工具只需要补充询问未提供的信息：

```
根据你的需求（Python技术栈 + Anthropic模型 + 编码助手），
我还需要确认：

1. Agent规模？
   - 小型：个人助手
   - 中型：团队工具
   - 大型：企业平台

2. 是否需要多Agent协作？
   - 是 / 否

请补充提供以上信息，我将开始构建。
```

### 默认值策略

如果用户没有明确偏好，AI coding工具可以建议默认值，但必须说明原因：

```
你未明确说明偏好，我将使用以下默认值：
- 技术栈：Python（功能完善，社区活跃）
- LLM供应商：Anthropic（长上下文优势）
- Agent规模：中型（平衡功能与复杂度）
- 主要用途：通用对话
- 多Agent协作：否

如果你有其他偏好，请在回复中说明，我会相应调整。
```

---

## 分阶段构建指南（v2核心改进）

> **重要：当用户说"帮我构建一个Agent"时，必须按以下7个阶段逐步执行。**
> **每个阶段完成后，必须检查检查清单，确认通过后再进入下一阶段。**

### Phase 1: 项目初始化（参考 references/01-phase-init.md）

**目标**：建立项目骨架，定义目录结构和配置文件

**理论指导**：
- 应用 **Context Engineering** 原则：目录结构即信息的可访问性
- 应用 **Architectural Constraints** 原则：通过目录结构建立边界

**实践步骤**：
1. 创建标准目录结构（src/、config/、skills/、memory/、workspace/、tests/）
2. 创建主配置文件 config/settings.yaml
3. 创建环境变量模板 .env.example
4. 创建项目 README.md

**检查清单**：
- [ ] 目录结构符合规范
- [ ] 配置文件包含LLM、Agent、工具、权限、记忆配置
- [ ] README包含安装、配置、启动说明
- [ ] .env.example包含所有必要的环境变量

**常见问题**：
- 问题：目录结构不清晰，核心代码和用户配置混在一起
- 解决：严格区分 src/（核心框架）和 config/（用户配置）

---

### Phase 2: LLM抽象层（参考 references/02-phase-llm.md）

**目标**：实现与供应商无关的LLM客户端抽象

**理论指导**：
- 应用 **供应商无关性** 原则：代码不绑定特定LLM供应商
- 应用 **工厂模式**：通过配置切换供应商

**实践步骤**：
1. 创建抽象LLM客户端接口 src/llm/client.py
2. 实现Anthropic客户端 src/llm/providers/anthropic.py
3. 实现OpenAI客户端 src/llm/providers/openai.py
4. 实现本地模型客户端 src/llm/providers/local.py
5. 创建工厂函数 src/llm/factory.py

**检查清单**：
- [ ] 抽象接口定义完整（chat、validate_config）
- [ ] 至少实现3个供应商（Anthropic、OpenAI、Local）
- [ ] 工厂函数支持通过配置切换供应商
- [ ] 代码中没有硬编码的供应商依赖

**常见问题**：
- 问题：默认使用Anthropic，用户想切换供应商需要改很多代码
- 解决：所有供应商相关配置都通过配置文件管理

---

### Phase 3: 工具系统（参考 references/03-phase-tools.md）

**目标**：实现模块化的工具注册和执行机制

**理论指导**：
- 应用 **工具分区算法**：只读工具可并发，写入工具需串行
- 应用 **Schema验证**：工具输入必须符合预定义Schema

**实践步骤**：
1. 创建工具注册表 src/tools/registry.py
2. 实现文件操作工具 src/tools/file_tools.py
3. 实现网络请求工具 src/tools/network_tools.py
4. 实现浏览器工具 src/tools/browser_tools.py（可选）

**检查清单**：
- [ ] 工具注册表支持动态注册和查询
- [ ] 每个工具都有完整的Schema定义
- [ ] 工具执行有错误处理
- [ ] 支持并发安全标记

**常见问题**：
- 问题：工具描述不清晰，LLM调用时参数错误
- 解决：工具描述要详细，包含参数说明和注意事项

---

### Phase 4: Agent核心循环（参考 references/04-phase-agent-loop.md）

**目标**：实现健壮的Agent主循环，包含错误恢复和状态管理

**理论指导**：
- 应用 **7个Continue站点**：从几乎任何错误中恢复
- 应用 **状态机设计**：单一State对象，伪不可变语义

**实践步骤**：
1. 创建Agent核心类 src/agent/core.py
2. 实现主循环（while true + 7个continue站点）
3. 实现状态管理 src/agent/session.py
4. 实现错误恢复机制

**检查清单**：
- [ ] 主循环包含7个continue站点
- [ ] 状态管理使用单一State对象
- [ ] 错误恢复机制覆盖常见错误
- [ ] 支持最大轮次限制

**常见问题**：
- 问题：遇到API错误时直接崩溃，没有重试
- 解决：实现渐进式降级，每种错误先尝试最轻量的恢复

---

### Phase 5: 上下文管理（参考 references/05-phase-context.md）

**目标**：实现四级压缩管道和记忆系统

**理论指导**：
- 应用 **四级压缩管道**：Snip → Microcompact → Context-Collapse → Autocompact
- 应用 **记忆四分类**：User、Feedback、Project、Reference

**实践步骤**：
1. 实现上下文管理器 src/agent/context.py
2. 实现四级压缩管道
3. 实现记忆系统 src/agent/memory.py
4. 实现自动做梦机制

**检查清单**：
- [ ] 四级压缩管道完整实现
- [ ] 压缩后恢复关键状态
- [ ] 记忆系统支持短期和长期记忆
- [ ] 自动做梦机制触发条件正确

**常见问题**：
- 问题：压缩后丢失关键上下文
- 解决：压缩后必须主动恢复文件内容、Skill上下文、Plan、任务列表

---

### Phase 6: 权限安全（参考 references/06-phase-permissions.md）

**目标**：实现完整的权限控制和沙箱机制

**理论指导**：
- 应用 **六层纵深防御**：权限模型、Hook系统、沙箱、审计
- 应用 ** deny > settings rules > hook allow**：安全不可变量

**实践步骤**：
1. 实现权限模型 src/permissions/models.py
2. 实现Hook系统 src/permissions/hooks.py
3. 实现沙箱管理 src/permissions/sandbox.py
4. 配置权限规则 config/settings.yaml

**检查清单**：
- [ ] 权限模型支持allow/deny/ask三种模式
- [ ] Hook系统支持pre/post-tool-use
- [ ] 沙箱限制文件系统访问范围
- [ ] 危险命令被正确拦截

**常见问题**：
- 问题：Hook allow绕过deny规则
- 解决：deny > settings rules > hook allow，这是安全不可变量

---

### Phase 7: 生产化（参考 references/07-phase-production.md）

**目标**：添加测试、监控、日志，使项目达到生产级标准

**理论指导**：
- 应用 **三级Harness成熟度**：个人 → 团队 → 组织级
- 应用 **三层测试金字塔**：单元测试、集成测试、端到端测试

**实践步骤**：
1. 编写单元测试 tests/test_*.py
2. 添加监控和日志 src/utils/logging.py
3. 添加性能监控
4. 编写部署文档

**检查清单**：
- [ ] 核心模块都有单元测试
- [ ] 日志系统支持多级别
- [ ] 性能监控记录关键指标
- [ ] 部署文档完整

**常见问题**：
- 问题：测试覆盖率低，关键路径未测试
- 解决：优先测试Agent核心循环和工具执行

## 十大设计哲学

1. **Async Generator流式架构**: 不是返回最终结果，而是yield每一个中间事件
2. **通过Continue站点实现状态机**: while(true) + 7个continue站点
3. **编译时特性门控**: if (feature('FEATURE_X')) // bun:bundle编译时求值
4. **缓存前缀稳定性**: 内置工具排序后作为稳定前缀，MCP工具变化不影响缓存
5. **纵深防御**: 6层叠加使绕过概率指数下降
6. **数据驱动的可扩展性**: settings.json + agents/*.md + skills/*.md + hooks
7. **上下文即稀缺资源**: 工具延迟加载、记忆按需附加、四级压缩管道
8. **层级化配置覆盖**: 7级设置，CLI > Flag > Policy > Managed > Local > Project > User
9. **隔离的子Agent上下文**: 子Agent从空白消息列表开始，完成后只返回摘要
10. **可逆性优先**: 文件编辑通过Edit（替换字符串），不是Write（覆盖）

## 常见陷阱

1. **不要在Stop hook中做太重的操作**: 可能触发prompt-too-long错误，导致逻辑被静默跳过
2. **Hook allow不能绕过deny规则**: deny > settings rules > hook allow，这是安全不可变量
3. **hasAttemptedReactiveCompact不重置**: 防止compact→仍然太长→error→stop hook→compact的无限循环
4. **数组合并策略是连接+去重，而非替换**: 权限规则需要累加而非覆盖
5. **沙盒设置文件被硬编码为不可写**: 防止Agent通过修改settings.json来关闭沙盒
6. **MCP工具默认使用always_ask**: 第三方工具不应被自动信任
7. **Prompt Cache有最小长度要求**: 约1024 token，太短的前缀不会被缓存
8. **上下文压缩后必须主动恢复关键状态**: 文件内容、Skill上下文、Plan、任务列表

## 参考资源

- **核心文档**: 本目录下的 `references/` 文件
- **项目模板**: `templates/project-scaffold/` 目录下的完整项目模板
- **README模板**: `templates/README.md`
- **外部资源**:
  - Anthropic Managed Agents API文档
  - Claude Code源码（~512,664行TypeScript）
  - MCP协议规范
  - "Scaling Managed Agents: Decoupling the brain from the hands" - Anthropic技术论文
