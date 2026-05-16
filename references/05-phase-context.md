# Phase 5: 上下文管理

## 目标

实现四级压缩管道和记忆系统，高效利用上下文窗口，避免API调用失败。

## 理论指导

### 应用的设计原则

1. **四级压缩管道**：Snip → Microcompact → Context-Collapse → Autocompact
   - 为什么：上下文窗口是稀缺资源，需要精细管理
   - 怎么做：渐进式压缩，先轻后重

2. **记忆四分类**：User、Feedback、Project、Reference
   - 为什么：不同类型的记忆有不同的生命周期
   - 怎么做：分类存储，按需加载

3. **上下文即稀缺资源**：工具延迟加载、记忆按需附加
   - 为什么：200K tokens很快会被用完
   - 怎么做：只在需要时加载工具和记忆

### 为什么需要四级压缩？

场景：Agent正在处理一个复杂任务，上下文已经接近200K限制
- 如果没有压缩：API调用失败，任务中断
- 如果有压缩：自动释放空间，任务继续

四级压缩策略：
1. **Snip**：移除最旧的消息（成本极低）
2. **Microcompact**：缩减工具结果（成本低）
3. **Context-Collapse**：读时投射（成本中）
4. **Autocompact**：LLM全对话摘要（成本高）

## 实践步骤

### 步骤1：实现上下文管理器

文件：`src/agent/context.py`

```python
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

@dataclass
class ContextWindow:
    """上下文窗口"""
    messages: List[Dict[str, str]] = field(default_factory=list)
    max_tokens: int = 200000
    current_tokens: int = 0

class ContextManager:
    """上下文管理器"""
    
    def __init__(self, max_tokens: int = 200000):
        self.max_tokens = max_tokens
        self.context = ContextWindow(max_tokens=max_tokens)
    
    def add_message(self, role: str, content: str):
        """添加消息到上下文"""
        self.context.messages.append({"role": role, "content": content})
        self.context.current_tokens += len(content) // 4  # 粗略估算
        
        # 检查是否需要压缩
        if self.context.current_tokens > self.max_tokens * 0.8:
            self.compact()
    
    def compact(self):
        """
        四级压缩管道：
        1. Snip - 移除最旧的消息
        2. Microcompact - 缩减工具结果
        3. Context-Collapse - 读时投射
        4. Autocompact - LLM全对话摘要
        """
        # Level 1: Snip
        if self._snip():
            return
        
        # Level 2: Microcompact
        if self._microcompact():
            return
        
        # Level 3: Context-Collapse
        if self._context_collapse():
            return
        
        # Level 4: Autocompact
        self._autocompact()
    
    def _snip(self) -> bool:
        """Level 1: 移除最旧的消息"""
        if len(self.context.messages) > 10:
            removed = self.context.messages[:len(self.context.messages) // 2]
            self.context.messages = self.context.messages[len(self.context.messages) // 2:]
            self.context.current_tokens -= sum(len(m["content"]) for m in removed) // 4
            return True
        return False
    
    def _microcompact(self) -> bool:
        """Level 2: 缩减工具结果"""
        for msg in self.context.messages:
            if len(msg["content"]) > 1000:
                msg["content"] = msg["content"][:500] + "... [truncated]"
        return True
    
    def _context_collapse(self) -> bool:
        """Level 3: 读时投射"""
        # 简化实现：保留关键消息
        return True
    
    def _autocompact(self):
        """Level 4: LLM全对话摘要"""
        # 简化实现：生成摘要
        pass
```

### 步骤2：实现记忆系统

文件：`src/agent/memory.py`

```python
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path

class MemoryManager:
    """记忆管理器"""
    
    def __init__(self, storage_path: str = "memory"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.short_term: List[Dict[str, Any]] = []
    
    def add_short_term(self, content: str, metadata: Dict[str, Any] = None):
        """添加短期记忆"""
        memory = {
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        self.short_term.append(memory)
    
    def add_long_term(self, category: str, content: str):
        """添加长期记忆"""
        memory_file = self.storage_path / f"{category}.md"
        
        with open(memory_file, "a") as f:
            f.write(f"\n## {datetime.now().isoformat()}\n\n")
            f.write(f"{content}\n\n")
    
    def get_relevant_memories(self, query: str, limit: int = 5) -> List[str]:
        """获取相关记忆"""
        # 简化实现：返回最近的记忆
        memories = []
        for memory in self.short_term[-limit:]:
            memories.append(memory["content"])
        return memories
    
    def consolidate(self):
        """整合记忆（自动做梦机制）"""
        # 将短期记忆转为长期记忆
        if len(self.short_term) > 10:
            consolidated = "\n".join(m["content"] for m in self.short_term)
            self.add_long_term("consolidated", consolidated)
            self.short_term = []
```

### 步骤3：集成到Agent核心

文件：`src/agent/core.py`（部分）

```python
from .context import ContextManager
from .memory import MemoryManager

class AgentCore:
    def __init__(self, llm_config: Dict[str, Any]):
        # ... 初始化LLM客户端 ...
        
        self.context_manager = ContextManager()
        self.memory_manager = MemoryManager()
    
    async def run(self, user_input: str) -> str:
        """运行Agent"""
        # 添加上下文
        self.context_manager.add_message("user", user_input)
        
        # 获取相关记忆
        memories = self.memory_manager.get_relevant_memories(user_input)
        if memories:
            self.context_manager.add_message("system", f"相关记忆: {memories}")
        
        # ... 调用LLM ...
```

## 检查清单

- [ ] 四级压缩管道完整实现
- [ ] 压缩后恢复关键状态
- [ ] 记忆系统支持短期和长期记忆
- [ ] 自动做梦机制触发条件正确
- [ ] 上下文窗口利用率监控
- [ ] 压缩策略可配置

## 常见问题

### 问题：压缩后丢失关键上下文

**症状**：
- Agent忘记之前的任务
- 文件内容丢失
- Skill上下文丢失

**解决**：
- 压缩后必须主动恢复关键状态
- 重新读取当前正在编辑的文件
- 重新加载正在使用的Skill指令

### 问题：记忆系统效率低

**症状**：
- 记忆检索慢
- 记忆不准确
- 记忆膨胀

**解决**：
- 使用向量数据库存储记忆
- 定期清理过期记忆
- 实现记忆去重

## 下一步

完成Phase 5后，进入 **Phase 6: 权限安全**（参考 `references/06-phase-permissions.md`）
