# Phase 2: LLM抽象层

## 目标

实现与供应商无关的LLM客户端抽象，让Agent能够无缝切换不同的LLM供应商。

## 理论指导

### 应用的设计原则

1. **供应商无关性（Provider Agnostic）**：代码不绑定特定LLM供应商
   - 为什么：避免被单一供应商锁定，支持灵活切换
   - 怎么做：抽象接口 + 工厂模式

2. **依赖倒置原则**：高层模块不依赖低层模块，都依赖抽象
   - 为什么：降低耦合，提高可测试性
   - 怎么做：`AgentCore` 依赖 `LLMClient` 接口，不依赖具体实现

### 为什么需要抽象层？

场景1：用户最初使用Anthropic，但后来发现OpenAI更适合
- 如果没有抽象层：需要修改所有调用Anthropic API的代码
- 如果有抽象层：只需要修改配置文件

场景2：用户想在本地测试，但部署到云端使用云端模型
- 如果没有抽象层：需要维护两套代码
- 如果有抽象层：通过环境变量切换

## 实践步骤

### 步骤1：定义抽象接口

文件：`src/llm/client.py`

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class Message:
    """标准化消息格式"""
    role: str
    content: str

@dataclass
class ToolCall:
    """标准化工具调用格式"""
    id: str
    name: str
    arguments: Dict[str, Any]

@dataclass
class LLMResponse:
    """标准化LLM响应格式"""
    content: str
    tool_calls: List[ToolCall] = field(default_factory=list)
    usage: Dict[str, int] = field(default_factory=dict)
    model: str = ""

class LLMClient(ABC):
    """LLM客户端抽象基类"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model = config.get("model")
        self.max_tokens = config.get("max_tokens", 4096)
        self.temperature = config.get("temperature", 0.7)
    
    @abstractmethod
    async def chat(
        self,
        messages: List[Message],
        tools: Optional[List[Dict]] = None,
        **kwargs
    ) -> LLMResponse:
        """发送聊天请求"""
        pass
    
    def validate_config(self) -> bool:
        """验证配置是否有效"""
        return True
```

### 步骤2：实现Anthropic客户端

文件：`src/llm/providers/anthropic.py`

```python
import anthropic
from typing import Dict, Any, Optional, List

from ..client import LLMClient, Message, ToolCall, LLMResponse

class AnthropicClient(LLMClient):
    """Anthropic Claude客户端"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.client = anthropic.AsyncAnthropic(
            api_key=config.get("api_key"),
            base_url=config.get("base_url")
        )
    
    async def chat(
        self,
        messages: List[Message],
        tools: Optional[List[Dict]] = None,
        **kwargs
    ) -> LLMResponse:
        """发送聊天请求"""
        # 转换消息格式
        anthropic_messages = []
        for msg in messages:
            anthropic_messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # 调用API
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            messages=anthropic_messages,
            tools=tools or [],
            **kwargs
        )
        
        # 解析响应
        content = ""
        tool_calls = []
        for block in response.content:
            if block.type == "text":
                content += block.text
            elif block.type == "tool_use":
                tool_calls.append(ToolCall(
                    id=block.id,
                    name=block.name,
                    arguments=block.input
                ))
        
        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            usage={
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens
            },
            model=response.model
        )
    
    def validate_config(self) -> bool:
        """验证配置"""
        return bool(self.config.get("api_key"))
```

### 步骤3：实现OpenAI客户端

文件：`src/llm/providers/openai.py`

```python
import json as json_mod
from typing import Dict, Any, Optional, List

import openai

from ..client import LLMClient, Message, ToolCall, LLMResponse

class OpenAIClient(LLMClient):
    """OpenAI GPT客户端"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.client = openai.AsyncOpenAI(
            api_key=config.get("api_key"),
            base_url=config.get("base_url")
        )
    
    async def chat(
        self,
        messages: List[Message],
        tools: Optional[List[Dict]] = None,
        **kwargs
    ) -> LLMResponse:
        """发送聊天请求"""
        # 转换消息格式
        openai_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        
        # 调用API
        response = await self.client.chat.completions.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            messages=openai_messages,
            tools=tools or [],
            **kwargs
        )
        
        # 解析响应
        message = response.choices[0].message
        content = message.content or ""
        tool_calls = []
        if message.tool_calls:
            for tc in message.tool_calls:
                tool_calls.append(ToolCall(
                    id=tc.id,
                    name=tc.function.name,
                    arguments=json_mod.loads(tc.function.arguments)
                ))
        
        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens
            },
            model=response.model
        )
    
    def validate_config(self) -> bool:
        """验证配置"""
        return bool(self.config.get("api_key"))
```

### 步骤4：实现本地模型客户端

文件：`src/llm/providers/local.py`

```python
from typing import Dict, Any, Optional, List

import httpx

from ..client import LLMClient, Message, ToolCall, LLMResponse

class LocalClient(LLMClient):
    """本地模型客户端（兼容OpenAI API）"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.base_url = config.get("base_url", "http://localhost:11434")
        self.client = httpx.AsyncClient()
    
    async def chat(
        self,
        messages: List[Message],
        tools: Optional[List[Dict]] = None,
        **kwargs
    ) -> LLMResponse:
        """发送聊天请求"""
        payload = {
            "model": self.model,
            "messages": [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ],
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }
        
        response = await self.client.post(
            f"{self.base_url}/v1/chat/completions",
            json=payload
        )
        response.raise_for_status()
        data = response.json()
        
        message = data["choices"][0]["message"]
        return LLMResponse(
            content=message.get("content", ""),
            tool_calls=[],  # 本地模型可能不支持工具调用
            usage=data.get("usage", {}),
            model=self.model
        )
    
    def validate_config(self) -> bool:
        """验证配置"""
        return bool(self.config.get("base_url"))
```

### 步骤5：创建工厂函数

文件：`src/llm/factory.py`

```python
from typing import Dict, Any

from .client import LLMClient
from .providers.anthropic import AnthropicClient
from .providers.openai import OpenAIClient
from .providers.local import LocalClient

def create_llm_client(config: Dict[str, Any]) -> LLMClient:
    """
    根据配置创建对应的LLM客户端
    
    Args:
        config: 配置字典，必须包含 provider 字段
        
    Returns:
        LLMClient实例
        
    Raises:
        ValueError: 如果供应商未知
    """
    provider = config.get("provider", "anthropic").lower()
    
    providers = {
        "anthropic": AnthropicClient,
        "openai": OpenAIClient,
        "azure": OpenAIClient,  # Azure使用OpenAI兼容API
        "local": LocalClient,
    }
    
    if provider not in providers:
        raise ValueError(
            f"Unknown provider: {provider}. "
            f"Supported: {', '.join(providers.keys())}"
        )
    
    client = providers[provider](config)
    
    if not client.validate_config():
        raise ValueError(f"Invalid configuration for provider: {provider}")
    
    return client
```

## 检查清单

- [ ] 抽象接口定义完整（chat、validate_config）
- [ ] 至少实现3个供应商（Anthropic、OpenAI、Local）
- [ ] 工厂函数支持通过配置切换供应商
- [ ] 代码中没有硬编码的供应商依赖
- [ ] 每个供应商客户端都有错误处理
- [ ] 支持工具调用（Anthropic和OpenAI）

## 常见问题

### 问题：默认使用Anthropic，用户想切换供应商需要改很多代码

**症状**：
- 代码中硬编码了 `import anthropic`
- 模型名称写死在代码中
- API调用方式与Anthropic强耦合

**原因**：
- 缺乏抽象层
- 没有使用工厂模式

**解决**：
- 使用 `LLMClient` 抽象接口
- 通过配置文件选择供应商
- 工厂函数根据配置创建对应客户端

### 问题：不同供应商的API格式不同

**症状**：
- Anthropic使用 `messages.create()`
- OpenAI使用 `chat.completions.create()`
- 工具调用格式不同

**解决**：
- 在供应商客户端内部处理格式转换
- 对外暴露统一的 `LLMResponse` 格式
- 工具调用使用标准 `ToolCall` 格式

### 问题：本地模型不支持工具调用

**症状**：
- 本地模型（如Ollama）不支持工具调用
- Agent无法执行工具

**解决**：
- 在 `LocalClient` 中返回空的 `tool_calls`
- 在Agent核心中处理无工具调用的情况
- 或者使用支持工具调用的本地模型（如vLLM）

## 下一步

完成Phase 2后，进入 **Phase 3: 工具系统**（参考 `references/03-phase-tools.md`）
