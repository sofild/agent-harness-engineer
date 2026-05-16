# 核心概念速查

## Harness Engineering 三大支柱

### Context Engineering（上下文工程）

管理信息的可访问性、结构和时机。

**静态上下文：**
- CLAUDE.md/AGENTS.md: 项目级持久上下文
- 设计文档: 架构决策、约束条件
- 代码规范: 命名约定、风格指南

**动态上下文：**
- 日志与指标: 运行时状态
- Git状态: 分支、变更、提交历史
- CI/CD状态: 构建结果、部署状态

**上下文压缩（四级管道）：**
```
Level 1: Snip（历史截断）
  - 成本：极低 | 延迟：~0ms
  - 释放少量token

Level 2: Microcompact（老化工具结果缩减）
  - 成本：低 | 延迟：~1ms
  - 边界消息延迟到API响应后

Level 3: Context-Collapse（读时投射，不修改数组）
  - 成本：中 | 延迟：~5ms
  - summary messages live in collapse store
  - 完全可逆，跨轮次持久化

Level 4: Autocompact（LLM全对话摘要）
  - 成本：高 | 延迟：~2s
  - 仅在前面三级无法解决问题时触发
```

**核心原则：** "Agent无法在上下文中访问的信息不存在"

### Architectural Constraints（架构约束）

通过机械执行而非建议来建立边界。

**权限模型：**
- 5种权限模式 × 7级规则层级
- Schema验证、并发安全标记
- 工具约束：只读/写入/破坏性分类

**安全边界：**
- 沙盒隔离：文件系统、网络、进程
- 硬编码拒绝：不可绕过的安全规则
- 纵深防御：6层叠加

### Entropy Management（熵管理）

定期清理Agent解决代码退化。

- 文档一致性验证
- 约束违规扫描
- 模式强制执行
- 依赖审计
- 性能监控
- 覆盖率守卫

## 三组件虚拟化架构

### Session（会话）

追加式事件日志（Append-only Event Log）。

**关键特性：**
- 不可变：只追加不修改
- 可序列化：JSONL格式
- 可回放：任何时刻可重建完整状态
- 类似数据库WAL，是系统的唯一事实来源

**事件类型：**
- `user_message`: 用户输入
- `assistant_text`: 模型生成文本
- `tool_use`: 工具调用
- `tool_result`: 工具执行结果
- `turn_start`/`turn_end`: 轮次边界

### Harness（编排器）

无状态编排循环。

**设计原则：**
- 全部输入来自Session日志
- 可随时崩溃、重启、迁移
- 给定同样的Session日志，任何实例都会做出同样决策
- 不持有任何本地状态

**核心循环：**
```
while (true) {
    // 1. 压缩管道（四级）
    // 2. 构建系统提示 + 规范化消息
    // 3. 调用 LLM API（流式）
    // 4. 收集 tool_use 块
    // 5. 错误恢复（7个continue站点）
    // 6. 工具执行（并发/串行分区）
    // 7. Stop Hook → 终止或继续
    // 8. 更新状态 → continue
}
```

### Sandbox（沙箱）

隔离执行环境。

**三层隔离：**
1. **文件系统隔离**: Agent只能访问为其分配的工作目录
2. **网络隔离**: 默认禁止出站网络，通过白名单控制
3. **进程隔离**: PID Namespace + cgroups资源控制

**凭证生命周期：**
```
创建 → 存储（加密）→ 注入（只读挂载）→ 使用 → 轮换 → 吊销
```

## 系统提示工程

### 四维框架

| 维度 | 核心问题 | 缺失后果 |
|------|---------|---------|
| 角色 (Role) | 我是谁？ | 回答风格不稳定 |
| 能力 (Capability) | 我能做什么？ | 过度承诺或过度保守 |
| 约束 (Constraint) | 我不能做什么？ | 越界操作，安全风险 |
| 输出格式 (Format) | 我如何表达？ | 输出不一致，下游解析失败 |

### 约束的三个层次

- **硬约束**: 绝对不能违反的规则（"永远不要执行rm -rf /"）
- **软约束**: 默认遵守但可被用户显式覆盖（"默认创建新commit而不是amend"）
- **条件约束**: 在特定场景下触发的规则（"如果检测到敏感信息，立即停止"）

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
