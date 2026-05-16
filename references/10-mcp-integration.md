# MCP集成

## MCP协议概述

MCP（Model Context Protocol）是Anthropic提出的开放协议，用于标准化AI模型与外部工具、数据源之间的集成。

### 核心概念

- **Server**：提供工具和数据的服务端
- **Client**：使用工具和数据的客户端（即Agent）
- **Tool**：Agent可以调用的功能
- **Resource**：Agent可以访问的数据

### 六种传输协议

| 协议 | 说明 | 适用场景 |
|------|------|---------|
| stdio | 标准输入输出 | 本地工具 |
| HTTP | HTTP请求 | 远程API |
| SSE | Server-Sent Events | 实时数据流 |
| WebSocket | 全双工通信 | 实时交互 |
| gRPC | 高性能RPC | 微服务 |
| Local | 本地函数调用 | 同进程 |

## MCP配置示例

### 配置文件

文件：`config/mcp.json`

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/files"]
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}"
      }
    },
    "postgres": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres", "postgresql://localhost/mydb"]
    }
  }
}
```

### 客户端集成

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class MCPClient:
    def __init__(self, server_params):
        self.server_params = server_params
        self.session = None
    
    async def connect(self):
        """连接到MCP服务器"""
        self.read, self.write = await stdio_client(self.server_params)
        self.session = await ClientSession(self.read, self.write).__aenter__()
        await self.session.initialize()
    
    async def list_tools(self):
        """列出可用工具"""
        return await self.session.list_tools()
    
    async def call_tool(self, name, arguments):
        """调用工具"""
        return await self.session.call_tool(name, arguments)
    
    async def close(self):
        """关闭连接"""
        if self.session:
            await self.session.__aexit__(None, None, None)
```

## 工具集成

### 文件系统工具

```python
# 使用MCP文件系统工具
async def read_file_with_mcp(client, path):
    result = await client.call_tool("read_file", {"path": path})
    return result.content
```

### GitHub工具

```python
# 使用MCP GitHub工具
async def create_issue_with_mcp(client, repo, title, body):
    result = await client.call_tool("create_issue", {
        "repo": repo,
        "title": title,
        "body": body
    })
    return result.content
```

## 最佳实践

1. **错误处理**：MCP调用可能失败，需要重试
2. **超时控制**：设置合理的超时时间
3. **资源清理**：及时关闭连接
4. **并发控制**：限制并发连接数
5. **监控**：记录MCP调用指标
