# Phase 3: 工具系统

## 目标

实现模块化的工具注册和执行机制，让Agent能够调用各种工具完成任务。

## 理论指导

### 应用的设计原则

1. **工具分区算法**：只读工具可并发，写入工具需串行
   - 为什么：提高性能，避免数据竞争
   - 怎么做：标记工具的并发安全性

2. **Schema验证**：工具输入必须符合预定义Schema
   - 为什么：减少LLM调用时的参数错误
   - 怎么做：使用JSON Schema定义工具参数

3. **延迟加载**：工具按需加载，不占用上下文空间
   - 为什么：上下文窗口是稀缺资源
   - 怎么做：工具定义只在需要时传给LLM

### 为什么需要工具系统？

场景1：Agent需要读取文件
- 如果没有工具系统：Agent只能生成文本，无法与文件系统交互
- 如果有工具系统：Agent可以调用 `read_file` 工具读取文件

场景2：Agent需要执行命令
- 如果没有工具系统：Agent无法执行任何命令
- 如果有工具系统：Agent可以调用 `bash` 工具执行命令

## 实践步骤

### 步骤1：创建工具注册表

文件：`src/tools/registry.py`

```python
import json
from typing import Dict, List, Any, Callable
from dataclasses import dataclass

@dataclass
class ToolDefinition:
    """工具定义"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    handler: Callable
    is_concurrency_safe: bool = False

class ToolRegistry:
    """工具注册表"""
    
    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}
    
    def register(self, name: str, description: str, input_schema: Dict[str, Any], 
                 handler: Callable, is_concurrency_safe: bool = False):
        """
        注册工具
        
        Args:
            name: 工具名称
            description: 工具描述
            input_schema: 输入参数Schema
            handler: 处理函数
            is_concurrency_safe: 是否支持并发执行
        """
        self._tools[name] = ToolDefinition(
            name=name,
            description=description,
            input_schema=input_schema,
            handler=handler,
            is_concurrency_safe=is_concurrency_safe
        )
    
    def get_definitions(self) -> List[Dict[str, Any]]:
        """获取所有工具定义（用于LLM）"""
        return [
            {
                "type": "custom",
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.input_schema,
            }
            for tool in self._tools.values()
        ]
    
    def execute(self, name: str, input_data: Dict[str, Any]) -> Any:
        """
        执行工具
        
        Args:
            name: 工具名称
            input_data: 输入参数
            
        Returns:
            工具执行结果
            
        Raises:
            ValueError: 如果工具不存在
        """
        if name not in self._tools:
            raise ValueError(f"Unknown tool: {name}")
        
        tool = self._tools[name]
        return tool.handler(input_data)
    
    def list_tools(self) -> List[str]:
        """列出所有工具名称"""
        return list(self._tools.keys())
```

### 步骤2：实现文件操作工具

文件：`src/tools/file_tools.py`

```python
import os
from typing import Dict, Any

class FileTools:
    """文件操作工具"""
    
    # 工具Schema定义
    read_file_schema = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "文件路径"},
            "offset": {"type": "integer", "description": "起始行号（1-based）", "minimum": 1},
            "limit": {"type": "integer", "description": "最大读取行数", "minimum": 1, "maximum": 2000}
        },
        "required": ["path"]
    }
    
    write_file_schema = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "文件路径"},
            "content": {"type": "string", "description": "文件内容"}
        },
        "required": ["path", "content"]
    }
    
    def read_file(self, input_data: Dict[str, Any]) -> str:
        """读取文件内容"""
        path = input_data["path"]
        offset = input_data.get("offset", 1)
        limit = input_data.get("limit", 2000)
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                start = max(0, offset - 1)
                end = min(start + limit, len(lines))
                return ''.join(lines[start:end])
        except Exception as e:
            return f"Error: {str(e)}"
    
    def write_file(self, input_data: Dict[str, Any]) -> str:
        """写入文件内容"""
        path = input_data["path"]
        content = input_data["content"]
        
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"Successfully wrote to {path}"
        except Exception as e:
            return f"Error: {str(e)}"
```

### 步骤3：实现网络请求工具

文件：`src/tools/network_tools.py`

```python
import requests
from typing import Dict, Any

class NetworkTools:
    """网络操作工具"""
    
    web_fetch_schema = {
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "网页URL"},
            "selector": {"type": "string", "description": "CSS选择器（可选）"}
        },
        "required": ["url"]
    }
    
    http_request_schema = {
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "请求URL"},
            "method": {"type": "string", "description": "HTTP方法", "enum": ["GET", "POST", "PUT", "DELETE"]},
            "headers": {"type": "object", "description": "请求头"},
            "body": {"type": "string", "description": "请求体"}
        },
        "required": ["url", "method"]
    }
    
    def web_fetch(self, input_data: Dict[str, Any]) -> str:
        """获取网页内容"""
        url = input_data["url"]
        selector = input_data.get("selector")
        
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            if selector:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')
                elements = soup.select(selector)
                return "\n".join([e.get_text() for e in elements])
            
            return response.text
        except Exception as e:
            return f"Error: {str(e)}"
    
    def http_request(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """发送HTTP请求"""
        url = input_data["url"]
        method = input_data.get("method", "GET")
        headers = input_data.get("headers", {})
        body = input_data.get("body")
        
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=10)
            elif method == "POST":
                response = requests.post(url, headers=headers, data=body, timeout=10)
            elif method == "PUT":
                response = requests.put(url, headers=headers, data=body, timeout=10)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers, timeout=10)
            else:
                return {"error": f"Unsupported method: {method}"}
            
            return {
                "status": response.status_code,
                "headers": dict(response.headers),
                "body": response.text
            }
        except Exception as e:
            return {"error": str(e)}
```

### 步骤4：注册工具到Agent

文件：`src/agent/core.py`（部分）

```python
from ..tools.registry import ToolRegistry
from ..tools.file_tools import FileTools
from ..tools.network_tools import NetworkTools

class AgentCore:
    def __init__(self, llm_config: Dict[str, Any]):
        # ... 初始化LLM客户端 ...
        
        self.tools = ToolRegistry()
        self._register_default_tools()
    
    def _register_default_tools(self):
        """注册默认工具"""
        file_tools = FileTools()
        network_tools = NetworkTools()
        
        # 注册文件工具（只读，可并发）
        self.tools.register(
            "read_file", 
            "读取文件内容", 
            file_tools.read_file_schema,
            file_tools.read_file,
            is_concurrency_safe=True
        )
        
        # 注册文件工具（写入，需串行）
        self.tools.register(
            "write_file",
            "写入文件内容",
            file_tools.write_file_schema,
            file_tools.write_file,
            is_concurrency_safe=False
        )
        
        # 注册网络工具
        self.tools.register(
            "web_fetch",
            "获取网页内容",
            network_tools.web_fetch_schema,
            network_tools.web_fetch,
            is_concurrency_safe=True
        )
```

## 检查清单

- [ ] 工具注册表支持动态注册和查询
- [ ] 每个工具都有完整的Schema定义
- [ ] 工具执行有错误处理
- [ ] 支持并发安全标记
- [ ] 工具描述清晰，包含参数说明
- [ ] 工具返回格式统一

## 常见问题

### 问题：工具描述不清晰，LLM调用时参数错误

**症状**：
- LLM调用工具时缺少必要参数
- LLM传递了错误类型的参数
- 工具执行失败

**原因**：
- 工具描述不够详细
- Schema定义不完整
- 缺少参数示例

**解决**：
- 工具描述要详细，包含参数说明
- Schema定义要完整，包含类型、描述、约束
- 提供参数示例

### 问题：工具执行失败没有错误处理

**症状**：
- 工具执行失败时Agent崩溃
- 错误信息不清晰
- 无法从错误中恢复

**解决**：
- 工具函数内部使用try-except
- 返回友好的错误信息
- Agent核心捕获工具异常

### 问题：工具并发执行导致数据竞争

**症状**：
- 多个工具同时写入同一文件
- 工具执行顺序不确定
- 数据不一致

**解决**：
- 标记工具的并发安全性
- 只读工具可并发，写入工具需串行
- 使用工具分区算法

## 下一步

完成Phase 3后，进入 **Phase 4: Agent核心循环**（参考 `references/04-phase-agent-loop.md`）
