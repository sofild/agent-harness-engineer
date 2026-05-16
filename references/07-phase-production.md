# Phase 7: 生产化

## 目标

添加测试、监控、日志，使项目达到生产级标准。

## 理论指导

### 应用的设计原则

1. **三级Harness成熟度**：个人 → 团队 → 组织级
   - 为什么：不同阶段有不同的要求
   - 怎么做：逐步完善

2. **三层测试金字塔**：单元测试、集成测试、端到端测试
   - 为什么：不同层次的测试有不同的目的
   - 怎么做：优先单元测试，控制端到端测试数量

3. **可观测性内建**：每个恢复点都有analytics和profiling
   - 为什么：生产环境需要监控
   - 怎么做：内建监控和日志

## 实践步骤

### 步骤1：编写测试

文件：`tests/test_agent.py`

```python
import pytest
from unittest.mock import AsyncMock, MagicMock

from src.agent.core import AgentCore
from src.llm.client import LLMResponse, Message

@pytest.fixture
def mock_llm_client():
    client = MagicMock()
    client.chat = AsyncMock(return_value=LLMResponse(
        content="Test response",
        tool_calls=[],
        usage={},
        model="test-model"
    ))
    return client

@pytest.fixture
def agent(mock_llm_client):
    agent = AgentCore(llm_config={
        "provider": "anthropic",
        "model": "test-model",
        "api_key": "test-key"
    })
    agent.llm_client = mock_llm_client
    return agent

@pytest.mark.asyncio
async def test_agent_run(agent, mock_llm_client):
    result = await agent.run("Hello")
    assert result == "Test response"
    mock_llm_client.chat.assert_called_once()

@pytest.mark.asyncio
async def test_agent_reset(agent):
    agent.state.messages.append(Message(role="user", content="test"))
    agent.reset()
    assert len(agent.state.messages) == 0
    assert agent.state.turn_count == 0
```

### 步骤2：添加监控和日志

文件：`src/utils/logging.py`

```python
import os
import logging
from pathlib import Path

def setup_logging(level: str = None):
    if level is None:
        level = os.getenv("LOG_LEVEL", "info").upper()
    
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_dir / "agent.log")
        ]
    )

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
```

### 步骤3：添加性能监控

文件：`src/utils/monitoring.py`

```python
import time
from typing import Dict, Any, List

class MetricsCollector:
    """性能监控"""
    
    def __init__(self):
        self.metrics: List[Dict[str, Any]] = []
    
    def record(self, metric: Dict[str, Any]):
        self.metrics.append(metric)
    
    def summary(self) -> Dict[str, Any]:
        if not self.metrics:
            return {}
        
        return {
            "total_requests": len(self.metrics),
            "avg_latency": sum(m["latency"] for m in self.metrics) / len(self.metrics),
            "total_errors": sum(1 for m in self.metrics if m.get("error")),
            "error_rate": sum(1 for m in self.metrics if m.get("error")) / len(self.metrics)
        }
```

## 检查清单

- [ ] 核心模块都有单元测试
- [ ] 日志系统支持多级别
- [ ] 性能监控记录关键指标
- [ ] 部署文档完整
- [ ] CI/CD配置
- [ ] 安全审计通过

## 常见问题

### 问题：测试覆盖率低

**症状**：
- 关键路径未测试
- 测试用例不足

**解决**：
- 优先测试Agent核心循环
- 优先测试工具执行
- 使用Mock隔离外部依赖

### 问题：日志过多或过少

**症状**：
- 日志过多影响性能
- 日志过少无法定位问题

**解决**：
- 使用分级日志
- 生产环境使用WARN级别
- 开发环境使用DEBUG级别

## 完成！

恭喜！你已经完成了Agent系统的7个阶段构建。

### 下一步

- **优化**：参考 `references/09-agent-optimization.md` 进行性能优化
- **扩展**：参考 `references/10-mcp-integration.md` 集成MCP工具
- **部署**：参考 `references/08-production.md` 进行生产化部署
