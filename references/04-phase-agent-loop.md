# Phase 4: Agent核心循环

## 目标

实现健壮的Agent主循环，包含错误恢复和状态管理。这是Agent系统的核心，决定了Agent的稳定性和可靠性。

## 理论指导

### 应用的设计原则

1. **7个Continue站点**：从几乎任何错误中恢复
   - 为什么：Agent需要稳定运行，不能因为一次错误就崩溃
   - 怎么做：在关键路径上设置恢复点

2. **状态机设计**：单一State对象，伪不可变语义
   - 为什么：状态管理清晰，易于调试
   - 怎么做：每次迭代开始时解构State，在continue站点整体重新赋值

3. **流式优先**：Async Generator使每个中间状态都可观察
   - 为什么：实时反馈，用户体验更好
   - 怎么做：使用yield返回中间事件

### 为什么需要7个Continue站点？

场景：Agent正在处理一个复杂任务，突然遇到API错误
- 如果没有错误恢复：Agent崩溃，用户需要重新开始
- 如果有错误恢复：Agent自动重试，用户无感知

7个Continue站点：
1. **Proactive Compaction**：上下文过长时主动压缩
2. **Prompt Too Long**：API返回413错误时恢复
3. **Max Output Tokens**：输出被截断时升级
4. **Fallback Model**：主模型不可用时切换
5. **Stop Hook Blocking**：Hook要求额外轮次
6. **Image/Media Errors**：图片过大时移除
7. **Tool Execution**：正常工具执行完成

## 实践步骤

### 步骤1：定义状态类型

文件：`src/agent/core.py`（部分）

```python
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

@dataclass
class AgentState:
    """Agent状态"""
    messages: List[Dict[str, str]] = field(default_factory=list)
    turn_count: int = 0
    max_turns: int = 50
    stopped: bool = False
    last_error: Optional[str] = None
    has_attempted_reactive_compact: bool = False

class AgentCore:
    def __init__(self, llm_config: Dict[str, Any]):
        self.llm_client = create_llm_client(llm_config)
        self.state = AgentState()
        self.tools = ToolRegistry()
        self._register_default_tools()
```

### 步骤2：实现主循环

文件：`src/agent/core.py`（核心循环）

```python
import asyncio
from typing import Dict, Any, Optional

class AgentCore:
    # ... 初始化代码 ...
    
    async def run(self, user_input: str) -> str:
        """
        运行Agent主循环
        
        这是Agent的核心，包含7个Continue站点
        """
        # 添加用户消息
        self.state.messages.append({"role": "user", "content": user_input})
        self.state.turn_count += 1
        
        # 检查轮次限制
        if self.state.turn_count > self.state.max_turns:
            return "Error: Maximum turns reached"
        
        while True:
            try:
                # 步骤1: 压缩管道（四级）
                # 参考 Phase 5: 上下文管理
                self._compact_context()
                
                # 步骤2: 调用LLM
                response = await self.llm_client.chat(
                    messages=self.state.messages,
                    tools=self.tools.get_definitions()
                )
                
                # 步骤3: 处理响应
                if response.tool_calls:
                    # 有工具调用，执行工具
                    tool_results = await self._execute_tools(response.tool_calls)
                    
                    # 添加工具结果到消息
                    self.state.messages.append({
                        "role": "user",
                        "content": self._format_tool_results(tool_results)
                    })
                    
                    # Continue站点7: 工具执行完成，继续循环
                    continue
                
                # 没有工具调用，返回文本结果
                return response.content
                
            except Exception as e:
                # 错误恢复
                if not self._handle_error(e):
                    return f"Error: {e}"
    
    def _compact_context(self):
        """压缩上下文（简化版）"""
        # 参考 Phase 5: 上下文管理
        # 这里简化处理，实际应实现四级压缩
        if len(self.state.messages) > 20:
            # 保留最近的消息
            self.state.messages = self.state.messages[-10:]
    
    async def _execute_tools(self, tool_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """执行工具调用"""
        results = []
        
        for tool_call in tool_calls:
            try:
                result = self.tools.execute(tool_call["name"], tool_call["arguments"])
                results.append({
                    "tool_use_id": tool_call["id"],
                    "content": str(result),
                    "success": True
                })
            except Exception as e:
                results.append({
                    "tool_use_id": tool_call["id"],
                    "content": f"Error: {e}",
                    "success": False
                })
        
        return results
    
    def _format_tool_results(self, results: List[Dict[str, Any]]) -> str:
        """格式化工具结果"""
        return "\n".join([f"Tool {r['tool_use_id']}: {r['content']}" for r in results])
    
    def _handle_error(self, error: Exception) -> bool:
        """
        处理错误
        
        Returns:
            True if recovered, False if unrecoverable
        """
        error_str = str(error).lower()
        
        # Continue站点2: Prompt Too Long
        if "prompt too long" in error_str or "413" in error_str:
            self.state.has_attempted_reactive_compact = True
            self._compact_context()
            return True
        
        # Continue站点3: Max Output Tokens
        if "max output tokens" in error_str:
            # 增加max_tokens重试
            self.llm_client.max_tokens = min(self.llm_client.max_tokens * 2, 64000)
            return True
        
        # Continue站点4: Fallback Model
        if "model" in error_str and "unavailable" in error_str:
            # 切换到备用模型
            # 这里简化处理，实际应实现模型降级逻辑
            return False
        
        # 其他错误，记录并返回
        self.state.last_error = str(error)
        return False
```

### 步骤3：实现会话管理

文件：`src/agent/session.py`

```python
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

class SessionManager:
    """会话管理器"""
    
    def __init__(self, storage_path: str = "memory/sessions"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.current_session_id: Optional[str] = None
        self.events: List[Dict[str, Any]] = []
    
    def create_session(self) -> str:
        """创建新会话"""
        session_id = str(uuid.uuid4())
        self.current_session_id = session_id
        self.events = []
        return session_id
    
    def add_event(self, event_type: str, content: str, metadata: Dict[str, Any] = None):
        """添加事件"""
        event = {
            "id": str(uuid.uuid4()),
            "type": event_type,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        self.events.append(event)
        self._persist_event(event)
    
    def _persist_event(self, event: Dict[str, Any]):
        """持久化事件"""
        if not self.current_session_id:
            return
        
        session_file = self.storage_path / f"{self.current_session_id}.jsonl"
        with open(session_file, "a") as f:
            f.write(json.dumps(event) + "\n")
    
    def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        """获取会话历史"""
        session_file = self.storage_path / f"{session_id}.jsonl"
        if not session_file.exists():
            return []
        
        events = []
        with open(session_file, "r") as f:
            for line in f:
                events.append(json.loads(line))
        return events
```

## 检查清单

- [ ] 主循环包含7个continue站点
- [ ] 状态管理使用单一State对象
- [ ] 错误恢复机制覆盖常见错误
- [ ] 支持最大轮次限制
- [ ] 会话管理实现不可变日志
- [ ] 工具执行有错误处理
- [ ] 支持流式输出（可选）

## 常见问题

### 问题：遇到API错误时直接崩溃

**症状**：
- Agent遇到API错误时直接退出
- 用户需要重新开始
- 没有错误恢复

**原因**：
- 没有实现错误恢复机制
- 没有重试逻辑
- 没有降级策略

**解决**：
- 实现7个Continue站点
- 每种错误先尝试最轻量的恢复
- 逐步升级恢复策略

### 问题：状态管理混乱

**症状**：
- 状态分散在多个变量中
- 难以追踪状态变化
- 调试困难

**解决**：
- 使用单一State对象
- 伪不可变语义
- 状态显式化

### 问题：无限循环

**症状**：
- Agent陷入无限循环
- 不断调用工具
- 无法终止

**解决**：
- 设置最大轮次限制
- 检测循环模式
- 提供手动终止机制

## 下一步

完成Phase 4后，进入 **Phase 5: 上下文管理**（参考 `references/05-phase-context.md`）
